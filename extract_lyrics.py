import os
import re
import concurrent.futures
from typing import Tuple
from google import genai
from dotenv import load_dotenv

from services.transcription_service import TranscriptionService

# Tải các biến môi trường từ file .env lên
load_dotenv()

def extract_raw_lyrics(video_path):
    """
    Bước 1: Dùng TranscriptionService (in-memory cached Whisper / faster-whisper)
    trích xuất âm thanh thành văn bản từ video mà không cần nạp lại model từ ổ đĩa.
    """
    return TranscriptionService.transcribe(video_path)

def is_valid_lyrics(raw_text: str, ai_text: str) -> Tuple[bool, str]:
    """
    Đánh giá văn bản Whisper thô và kết quả AI để xác định xem có lời bài hát thực sự hay không.
    Trả về: (has_lyrics: bool, clean_text: str)
    """
    if not raw_text or not raw_text.strip():
        return False, ""

    # Loại bỏ các ký tự nhiễu, nốt nhạc, dấu câu lặp lại
    cleaned_raw = re.sub(r'[\s\.\,\!\?\♪\♫\-\_\(\)\[\]\:\;\/\\\'\"]+', '', raw_text)
    if not cleaned_raw:
        return False, ""

    if not ai_text or not ai_text.strip():
        return False, ""

    ai_lower = ai_text.strip().lower()

    # Danh sách các cụm từ từ chối / giải thích thường gặp của Gemini khi không có lời bài hát
    disclaimer_phrases = [
        'không có nội dung lời bài hát',
        'không chứa lời bài hát',
        'không thể nhận diện',
        'chỉ là các tiếng',
        'chỉ là tiếng',
        'tiếng lầm bầm',
        'không có lời',
        'đoạn âm thanh không chứa',
        'phần âm thanh thô bạn cung cấp chỉ là',
        'không có bài hát',
        'không nhận diện được lời',
        'không có lời thoại',
        'đoạn văn bản cung cấp không chứa lời bài hát'
    ]
    for phrase in disclaimer_phrases:
        if phrase in ai_lower:
            return False, ""

    # Kiểm tra nếu toàn bộ câu trả lời bị bọc trong ngoặc đơn hoặc ngoặc vuông chú thích
    stripped = ai_text.strip()
    if (stripped.startswith('(') and stripped.endswith(')')) or (stripped.startswith('[') and stripped.endswith(']')):
        return False, ""

    return True, stripped

def clean_lyrics_with_ai(raw_lyrics):
    """
    Bước 2: Dùng Gemini AI làm sạch lyrics với giới hạn timeout 15s.
    Trả về tuple: (lyrics_đã_xử_lý, nguồn_gốc) 
    với nguồn gốc là 'AI', 'Original' (lời gốc), hoặc 'None'.
    """
    if not raw_lyrics or not raw_lyrics.strip():
        return "", "None"

    # Kiểm tra nhanh nếu Whisper chỉ nhận diện ký tự nhiễu / nốt nhạc
    is_raw_valid, _ = is_valid_lyrics(raw_lyrics, raw_lyrics)
    if not is_raw_valid:
        return "", "None"

    # Lấy API Key từ biến môi trường hệ thống
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Không tìm thấy GEMINI_API_KEY trong biến môi trường hoặc file .env!")
        valid, val_text = is_valid_lyrics(raw_lyrics, raw_lyrics)
        return (val_text, "Original") if valid else ("", "None")

    # Khởi tạo client với api_key vừa lấy
    client = genai.Client(api_key=api_key)

    prompt = f"""
Bạn là một biên tập viên văn bản. Dưới đây là đoạn lời bài hát/âm thanh thô chưa được ngắt dòng do Whisper nhận diện.
Nhiệm vụ của bạn CHỈ là ngắt dòng và chia đoạn cho dễ đọc dựa trên chính văn bản đầu vào.

QUY TẮC BẮT BUỘC:
1. GIỮ NGUYÊN TỪ NGỮ ĐẦU VÀO: Không thay thế từ ngữ, không đổi nghĩa, không tự ý lấy lời đầy đủ của bài hát gốc nếu không có trong văn bản đầu vào, và không thêm bớt câu chữ mới.
2. CHỈ NGẮT DÒNG: Thêm dấu xuống dòng (\n) tại các điểm ngắt nhịp, hết vế hoặc hết câu hợp lý; có thể chèn thêm một dòng trống giữa các đoạn/khổ nếu cần để dễ nhìn.
3. LOẠI BỎ RÁC RÕ RÀNG (NẾU CÓ): Chỉ xóa các câu chào hỏi, kêu gọi đăng ký/subscribe hoặc quảng cáo kênh không thuộc lời bài hát.
4. TRẢ VỀ THUẦN VĂN BẢN: Chỉ xuất ra phần văn bản đã được ngắt dòng, không thêm lời mở đầu, giải thích hay tiêu đề. Nếu không có lời bài hát mà chỉ là tiếng ồn hoặc nhạc không lời, chỉ cần trả về rỗng.

Văn bản đầu vào:
----------------
{raw_lyrics}
----------------
"""

    models_to_try = [
          'gemini-2.5-flash', 
        'gemini-2.5-flash-lite', 
        'gemini-3.8-flash', 
        'gemini-3.6-flash', 
        'gemini-3-flash-preview', 
        'gemini-3.5-flash-lite'
    ]

    def _call_gemini():
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                cleaned_text = response.text.strip() if response.text else ""
                if cleaned_text:
                    valid, val_lyrics = is_valid_lyrics(raw_lyrics, cleaned_text)
                    if valid:
                        return val_lyrics, "AI"
                    else:
                        return "", "None"
            except Exception:
                continue
        valid, val_lyrics = is_valid_lyrics(raw_lyrics, raw_lyrics)
        return (val_lyrics, "Original") if valid else ("", "None")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_call_gemini)
    try:
        result = future.result(timeout=15.0)
        executor.shutdown(wait=False)
        return result
    except concurrent.futures.TimeoutError:
        print("⏱️ [Gemini AI] Quá thời gian chờ (15s), tự động fallback kiểm tra lời gốc từ Whisper...")
        executor.shutdown(wait=False, cancel_futures=True)
        valid, val_lyrics = is_valid_lyrics(raw_lyrics, raw_lyrics)
        return (val_lyrics, "Original") if valid else ("", "None")
    except Exception as e:
        print(f"⚠️ [Gemini AI] Lỗi gọi API: {e}")
        executor.shutdown(wait=False)
        valid, val_lyrics = is_valid_lyrics(raw_lyrics, raw_lyrics)
        return (val_lyrics, "Original") if valid else ("", "None")

def get_first_line(lyrics_text, max_length=100, min_length=50):
    """
    Bước 3: Lấy câu đầu (hoặc gộp thêm câu tiếp theo nếu quá ngắn) và giới hạn ký tự.
    Cắt theo từ hoàn chỉnh cuối cùng nằm trong phạm vi max_length.
    """
    if not lyrics_text:
        return ""
        
    # Lọc ra danh sách các dòng có nội dung
    lines = [line.strip() for line in lyrics_text.split('\n') if line.strip()]
    if not lines:
        return lyrics_text.strip()
    
    # Gom các câu lại với nhau cho đến khi đạt độ dài tối thiểu (min_length) hoặc hết dòng
    combined_text = ""
    for line in lines:
        if not combined_text:
            combined_text = line
        else:
            # Nếu câu hiện tại chưa đủ độ dài tối thiểu, gộp thêm câu tiếp theo (ngăn cách bằng khoảng trắng)
            if len(combined_text) < min_length:
                combined_text += ". " + line
            else:
                break
                
    # Nếu đoạn text gộp lại vẫn vượt quá giới hạn max_length thì tiến hành cắt gọn theo từ
    if len(combined_text) > max_length:
        truncated = combined_text[:max_length]
        
        # Tìm khoảng trắng cuối cùng trong đoạn đã cắt để giữ lại trọn vẹn từ cuối
        last_space = truncated.rfind(' ')
        if last_space != -1:
            truncated = truncated[:last_space]
            
        combined_text = truncated.strip() + "..."
        
    return combined_text

def process_video_to_perfect_lyrics(video_path, max_length=100):
    """
    Hàm tổng hợp chính: Trích xuất -> Làm sạch bằng AI (có fallback) -> Lấy câu đầu tiên.
    Trả về dictionary chứa kết quả đầy đủ để dễ kiểm tra nguồn gốc.
    """
    raw_text = extract_raw_lyrics(video_path)
    if not raw_text:
        return {"first_line": "", "full_lyrics": "", "source": "None", "has_lyrics": False}
        
    cleaned_lyrics, source_type = clean_lyrics_with_ai(raw_text)
    has_lyrics = bool(source_type in ("AI", "Original") and cleaned_lyrics and cleaned_lyrics.strip())
    short_title = get_first_line(cleaned_lyrics, max_length) if has_lyrics else ""
    
    return {
        "first_line": short_title,     # Câu đầu tiên dùng để đặt tên file hoặc chèn video
        "full_lyrics": cleaned_lyrics,   # Toàn bộ lời bài hát đã làm sạch
        "source": source_type,           # 'AI', 'Original' hoặc 'None'
        "has_lyrics": has_lyrics
    }

if __name__ == "__main__":
    test_text = "Là hai sinh linh trót quen thân thế gian\nThế nhưng dở dang, giấu anh vào trang"
    print(get_first_line(test_text, 100, 50))

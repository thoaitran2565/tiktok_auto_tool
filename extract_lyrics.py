import os
import concurrent.futures
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

def clean_lyrics_with_ai(raw_lyrics):
    """
    Bước 2: Dùng Gemini AI làm sạch lyrics với giới hạn timeout 15s.
    Trả về tuple: (lyrics_đã_xử_lý, nguồn_gốc) 
    với nguồn gốc là 'AI' hoặc 'Original' (lời gốc).
    """
    if not raw_lyrics:
        return "", "Original"

    # Lấy API Key từ biến môi trường hệ thống
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Không tìm thấy GEMINI_API_KEY trong biến môi trường hoặc file .env!")
        return raw_lyrics, "Original"

    # Khởi tạo client với api_key vừa lấy
    client = genai.Client(api_key=api_key)

    prompt = f"""
    Bạn là một chuyên gia âm nhạc và biên tập viên văn bản. Dưới đây là phần lời thô (raw lyrics) tương đối do AI (Whisper) nhận diện từ âm thanh video. 

    NHIỆM VỤ CỦA BẠN:
    1. **LỌC BỎ TẠP ÂM & QUẢNG CÁO:** Tự động loại bỏ hoàn toàn các câu chào hỏi, lời kêu gọi đăng ký kênh, subscribe, quảng cáo (ví dụ như các câu kêu gọi xem video, tên kênh rác không liên quan đến bài hát) nếu xuất hiện trong phần lời thô.
    2. **ƯU TIÊN TÌM BÀI HÁT GỐC:** Dựa vào phần lời bài hát còn lại (dù có thể bị nghe nhầm hoặc sai chính tả), hãy phán đoán xem đây là bài hát gốc nào. Nếu nhận ra chính xác bài hát đó, hãy lấy **toàn bộ phần lời chuẩn xác và đầy đủ nhất** của bài hát gốc.
    3. **XỬ LÝ KHI KHÔNG TÌM RA (LÀM SẠCH BẢO THỦ):** Nếu không xác định được bài hát gốc, hãy giữ nguyên ý nghĩa câu chữ gốc, sửa lỗi chính tả do nghe nhầm từ đồng âm, xóa từ lặp vô nghĩa do âm vang, ngắt dòng và chia khổ dễ đọc, tuyệt đối không tự sáng tác thêm nội dung mới.
    4. **ĐỊNH DẠNG TRẢ VỀ:** Chỉ trả về phần lời bài hát đã được làm sạch hoặc lấy chuẩn từ bài gốc, không kèm theo lời chào, không giải thích gì thêm, không ghi tên bài hát.

    Phần lời thô cần xử lý:
    ----------------
    {raw_lyrics}
    ----------------
    """

    models_to_try = [
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b',
        'gemini-2.5-flash'
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
                    return cleaned_text, "AI"
            except Exception:
                continue
        return raw_lyrics, "Original"

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_call_gemini)
    try:
        result = future.result(timeout=15.0)
        executor.shutdown(wait=False)
        return result
    except concurrent.futures.TimeoutError:
        print("⏱️ [Gemini AI] Quá thời gian chờ (15s), tự động fallback dùng lời gốc từ Whisper...")
        executor.shutdown(wait=False, cancel_futures=True)
        return raw_lyrics, "Original"
    except Exception as e:
        print(f"⚠️ [Gemini AI] Lỗi gọi API: {e}")
        executor.shutdown(wait=False)
        return raw_lyrics, "Original"

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
        return {"first_line": "", "full_lyrics": "", "source": "None"}
        
    cleaned_lyrics, source_type = clean_lyrics_with_ai(raw_text)
    short_title = get_first_line(cleaned_lyrics, max_length)
    
    return {
        "first_line": short_title,     # Câu đầu tiên dùng để đặt tên file hoặc chèn video
        "full_lyrics": cleaned_lyrics,   # Toàn bộ lời bài hát đã làm sạch
        "source": source_type            # 'AI' hoặc 'Original'
    }

if __name__ == "__main__":
    test_text = "Là hai sinh linh trót quen thân thế gian\nThế nhưng dở dang, giấu anh vào trang"
    print(get_first_line(test_text, 100, 50))

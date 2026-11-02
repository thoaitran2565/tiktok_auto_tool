import os
import whisper
from google import genai
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env lên
load_dotenv()

def extract_raw_lyrics(video_path):
    """
    Bước 1: Dùng Whisper trích xuất âm thanh thô thành văn bản từ video.
    """
    if not os.path.exists(video_path):
        print(f"❌ Không tìm thấy file video tại: {video_path}")
        return None

    print("🚀 Đang chạy Whisper để trích xuất âm thanh thô từ video...")
    model = whisper.load_model("small")
    result = model.transcribe(video_path, task="transcribe")
    return result.get("text", "").strip()

def clean_lyrics_with_ai(raw_lyrics):
    """
    Bước 2: Dùng Gemini AI làm sạch lyrics. 
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
    Bạn là một biên tập viên văn bản âm nhạc. Dưới đây là phần lời thô (raw lyrics) do AI (Whisper) nhận diện từ âm thanh. 
    Nhiệm vụ của bạn là **làm sạch văn bản một cách cực kỳ bảo thủ**, tuân thủ nghiêm ngặt các quy tắc sau:

    QUY TẮC BẮT BUỘC:
    1. **TUYỆT ĐỐI KHÔNG SÁNG TÁC MỚI, KHÔNG ĐỔI NGHĨA:** Giữ nguyên ý nghĩa, câu chữ gốc của bài hát nhiều nhất có thể. Không được tự ý thay thế bằng từ ngữ hay hơn nếu từ gốc đã có nghĩa.
    2. **CHỈ SỬA LỖI CHÍNH TẢ DO AI NGHE NHẦM:** Whisper thường nghe nhầm các từ đồng âm. Hãy sửa lại các từ bị sai lỗi chính tả/nghe nhầm đó cho đúng với thực tế ngữ cảnh tiếng Việt.
    3. **XÓA TỪ LẶP DO LỖI NHẬN DIỆN:** Whisper hay bị lỗi lặp từ ngớ ngẩn do âm vang. Hãy dọn sạch các từ lặp vô nghĩa này.
    4. **NGẮT DÒNG VÀ CHIA KHỔ:** Chỉ làm nhiệm vụ xuống dòng, ngắt câu thành từng câu hát/khổ thơ dựa trên nội dung thô đã có để nhìn dễ đọc hơn, không thêm thắt bất kỳ đoạn chữ nào không có trong bản thô.
    5. Chỉ trả về phần lời bài hát đã được làm sạch, không kèm theo lời chào hay giải thích gì thêm.

    Phần lời thô cần xử lý:
    ----------------
    {raw_lyrics}
    ----------------
    """

    models_to_try = ['gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3-flash-preview']
    
    for model_name in models_to_try:
        try:
            print(f"🤖 Đang thử gọi mô hình: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            print(f"✅ Thành công với mô hình: \n{response.text}")
            return response.text.strip(), "AI"
        except Exception as e:
            print(f"⚠️ Mô hình {model_name} gặp lỗi, đang thử mô hình tiếp theo...")
    
    # Nếu tất cả các model đều thất bại -> Trả về lời gốc của Whisper và đánh dấu 'Original'
    print("❌ Tất cả các mô hình AI đều bận hoặc lỗi. Đang quay về sử dụng lyric thô gốc...")
    return raw_lyrics, "Original"

def get_first_line(lyrics_text, max_length=50):
    """
    Bước 3: Lấy câu đầu tiên từ văn bản lyrics và giới hạn ký tự.
    Cắt theo từ hoàn chỉnh cuối cùng nằm trong phạm vi max_length (tránh cắt ngang từ).
    """
    if not lyrics_text:
        return ""
        
    lines = [line.strip() for line in lyrics_text.split('\n') if line.strip()]
    first_line = lines[0] if lines else lyrics_text.strip()
    
    if len(first_line) > max_length:
        # Cắt tạm theo chiều dài tối đa cho phép
        truncated = first_line[:max_length]
        
        # Tìm khoảng trắng cuối cùng trong đoạn đã cắt để giữ lại trọn vẹn từ cuối
        last_space = truncated.rfind(' ')
        if last_space != -1:
            truncated = truncated[:last_space]
            
        first_line = truncated.strip() + "..."
        
    return first_line

def process_video_to_perfect_lyrics(video_path, max_length=50):
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

# --- KHU VỰC THỰC THI KIỂM TRA ---
if __name__ == "__main__":
    video_file = r"D:\Code\tools\tiktok_auto_tool\Videos\Đã đăng\CuocSongChill - 2026.11.1793520991927.mp4"
    
    result = process_video_to_perfect_lyrics(video_file, max_length=40)
    
    print("\n" + "="*20 + " KẾT QUẢ TRÍCH XUẤT LIRCYS " + "="*20)
    print(f"📌 Nguồn gốc trả ra : {result['source']} ('AI' hoặc 'Original')")
    print(f"📌 Câu đầu tiên     : {result['first_line']}")
    print(f"📌 Toàn bộ lyrics   :\n{result['full_lyrics']}")
    print("="*67)
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
        'gemini-2.5-flash', 
        'gemini-2.5-flash-lite', 
        'gemini-3.8-flash', 
        'gemini-3.6-flash', 
        'gemini-3-flash-preview', 
        'gemini-3.5-flash-lite'
    ]
    
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

# --- KHU VỰC THỰC THI KIỂM TRA ---
if __name__ == "__main__":
    # video_file = r"D:\Code\tools\tiktok_auto_render_tool\outputs\Em ơi đừng khóc bóng tối chốc lát sẽ bắt em đi.mp4"
    
    # result = process_video_to_perfect_lyrics(video_file, max_length=200)
    
    # print("\n" + "="*20 + " KẾT QUẢ TRÍCH XUẤT LIRCYS " + "="*20)
    # print(f"📌 Nguồn gốc trả ra : {result['source']} ('AI' hoặc 'Original')")
    # print(f"📌 Câu đầu tiên     : {result['first_line']}")
    # print(f"📌 Toàn bộ lyrics   :\n{result['full_lyrics']}")
    # print("="*67)
    a = get_first_line(
        """
Là hai sinh linh trót quen thân thế gian
Thế nhưng dở dang, giấu anh vào trang
Hồi kết mình chẳng thể cùng xem thêm

Em và anh thường viết nên những câu ca quen khi gảy đàn nghe
Luôn mong mình chạy xa qua đây, chắc tình ta chẳng hề
Mãi tới lần đầu tiên, hãy để lòng bình yên rồi đây
Chỉ có lời gửi tới em...

Chưa từng một ai nhớ về anh
Chưa khi nào một giờ ngừng nghĩ về em
Chưa từng một phút ngừng nhớ về anh
Chưa từng một giây nào yêu ai hơn em

Mà tình đẹp như bao hồi ức thật lâu
Ký tên của cuộc tình xưa đậm sâu
Cảm ơn ta đã gặp được nhau
Kiếp này sẽ nhớ, đã nhớ được gọi tên""",
        100, 
        50
    )

    print(a)
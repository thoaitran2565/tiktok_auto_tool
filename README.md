# 🎬 Tool Tự Động Render Video Hàng Loạt (Python & Flask)

Công cụ web local giúp tự động hóa quy trình tạo video ngắn (Reels, TikTok, Shorts) theo lô từ kho ảnh và kho video có sẵn. Tool tự động trích xuất âm thanh từ video gốc, ghép với ảnh ngẫu nhiên, định dạng khung hình chuẩn dọc điện thoại, lót nền đen, điều chỉnh độ sáng, chèn logo thương hiệu và tự động dọn dẹp (xóa) video nguồn sau khi xử lý xong.

---

## ✨ Các Tính Năng Chính

* **Giao diện Web Local (Dark Mode):** Trực quan, dễ sử dụng, hỗ trợ xem trước (preview) trực tiếp video và hình ảnh.
* **Xử lý tự động hàng loạt (Batch Processing):** Quét toàn bộ thư mục video và kho ảnh để tạo hàng đợi nhanh chóng.
* **Tùy chỉnh linh hoạt:** Cho phép xem trước danh sách hàng đợi và thay đổi ảnh ghép tùy ý cho từng video qua menu thả xuống (Dropdown).
* **Tự động trích xuất âm thanh:** Tự động chuyển đổi âm thanh từ video gốc thành MP3 và căn chỉnh thời lượng video đầu ra khớp tuyệt đối với âm thanh.
* **Định dạng chuẩn video ngắn (9:16):** Khung hình tự động quy chuẩn dọc điện thoại (`1080x1920`).
* **Xử lý hình ảnh thông minh:** 
  * Giữ nguyên tỷ lệ ảnh gốc (không bị bóp méo).
  * Tự động lót nền màu đen nếu ảnh không lấp đầy khung hình.
  * Tự động giảm **20% độ sáng** của ảnh nền giúp video có chiều sâu và làm nổi bật nội dung.
* **Chèn Logo Thương Hiệu:** Tự động gắn logo (`logo-text.png`) vào góc trên bên phải video.
* **Tối ưu dung lượng & giải phóng bộ nhớ:** Tự động **xóa video nguồn** ngay khi render xong để tiết kiệm dung lượng ổ cứng.
* **Tự động mở trình duyệt:** Tự động bật trang web ngay khi khởi động tool.

---

## 🛠 Yêu Cầu Hệ Thống

Trước khi chạy dự án, hãy đảm bảo máy tính của bạn đã cài đặt:
1. **Python** (Phiên bản 3.8 trở lên)
2. **FFmpeg** (Bắt buộc để xử lý video và âm thanh):
   * *Windows:* Cài đặt qua lệnh `winget install Gyan.FFmpeg` hoặc tải trực tiếp từ trang chủ.
   * *macOS:* Chạy lệnh `brew install ffmpeg`
   * *Linux:* Chạy lệnh `sudo apt install ffmpeg`

---

## 📦 Cài Đặt Thư Viện

Mở terminal/command prompt tại thư mục dự án và chạy lệnh sau để cài đặt các thư viện Python cần thiết:

```bash
pip install flask moviepy pillow numpy
```

---

## 📂 Cấu Trúc Thư Mục Dự Án

Hãy sắp xếp thư mục dự án của bạn theo cấu trúc sau:

```text
video_render_tool/
│
├── app.py                 # File mã nguồn chính Backend (Flask + MoviePy)
├── logo-text.png          # File logo thương hiệu (đặt ở góc phải trên video)
├── run_tool.bat           # File chạy nhanh 1-click (dành cho Windows)
├── outputs/               # Thư mục chứa các video sau khi render xong
└── templates/
    └── index.html         # Giao diện Web Local (Dark Mode)
```

---

## 🚀 Hướng Dẫn Sử Dụng

### Cách 1: Chạy nhanh bằng 1-click (Khuyên dùng trên Windows)
* Nhấp đúp chuột vào file **`run_tool.bat`**.
* Hệ thống sẽ khởi động server và **tự động mở trình duyệt web** cho bạn.

### Cách 2: Chạy thủ công qua Terminal
1. Mở terminal tại thư mục chứa dự án.
2. Chạy lệnh:
   ```bash
   python app.py
   ```
3. Mở trình duyệt web và truy cập thủ công vào địa chỉ:
   ```text
   http://127.0.0.1:5000/
   ```

---

## 📝 Các Bước Thao Tác Trên Giao Diện

1. **Nhập đường dẫn kho:** Nhập đường dẫn tuyệt đối đến thư mục chứa ảnh (Image Folder) và thư mục chứa video nguồn (Video Folder) của bạn vào giao diện.
2. **Quét hàng đợi:** Bấm nút **"Quét Thư Mục & Tạo Hàng Đợi"**. Hệ thống sẽ tải danh sách video và tự động ghép ngẫu nhiên với ảnh.
3. **Tùy chỉnh (Tùy chọn):** Tại bảng danh sách, bạn có thể xem trước video gốc, xem trước ảnh ghép và có thể đổi sang ảnh khác bất kỳ thông qua ô lựa chọn (Dropdown).
4. **Render tự động:** Bấm nút **"🚀 Bắt Đầu Render Tự Động Toàn Bộ"**. 
   * Thanh tiến trình thời gian thực sẽ hiển thị trên từng video.
   * Video gốc sẽ tự động bị xóa sau khi hoàn tất để giải phóng thư mục.
5. **Xem kết quả:** Khi video nào render xong, bạn có thể **phát xem trực tiếp ngay trên web** hoặc bấm **Tải xuống** để nhận file thành phẩm.
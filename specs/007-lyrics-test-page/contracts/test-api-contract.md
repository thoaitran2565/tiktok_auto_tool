# Interface Contracts: Lyrics Testing Page (/test)

**Feature**: `007-lyrics-test-page`  
**Date**: 2026-11-21  

---

## 1. Route: `GET /test`
Serves the testing single-page application.

- **Request**: `GET /test`
- **Response**: HTML document rendered from `templates/test.html`.
- **Status**: `200 OK`.

---

## 2. API: `POST /api/test-scan-videos`
Enumerates video files in a specified folder for lyrics testing.

- **Request Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "video_folder": "D:\\Media\\Videos"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "video_folder": "D:\\Media\\Videos",
    "total_videos": 12,
    "queue": [
      {
        "id": 0,
        "video_name": "sample_video_01.mp4",
        "video_path": "D:\\Media\\Videos\\sample_video_01.mp4",
        "duration_s": 35.0,
        "size_mb": 1.82,
        "status": "Chờ test",
        "raw_lyrics": "",
        "refined_lyrics": "",
        "lyric_source": "",
        "first_line": ""
      }
    ]
  }
  ```
- **Error Response** (`400 Bad Request`):
  ```json
  {
    "success": false,
    "error": "Thư mục video không hợp lệ hoặc không chứa video nào!"
  }
  ```

---

## 3. API: `POST /api/test-lyrics`
Executes isolated audio transcription and AI lyrics cleansing for a single video.

- **Request Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "video_path": "D:\\Media\\Videos\\sample_video_01.mp4",
    "item_id": 0
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "item_id": 0,
    "raw_lyrics": "Lời bài hát thô nhận diện từ Whisper...",
    "refined_lyrics": "Lời bài hát đã được làm sạch hoặc tìm bài gốc...",
    "lyric_source": "AI",
    "first_line": "Tên bài hát hoặc câu đầu",
    "has_lyrics": true,
    "duration_s": 35.0,
    "processing_time_s": 6.8
  }
  ```
- **Error Response** (`500 Internal Server Error`):
  ```json
  {
    "success": false,
    "item_id": 0,
    "error": "Video không có âm thanh hoặc định dạng không hỗ trợ!"
  }
  ```

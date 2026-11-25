# Quickstart Validation Guide: Lyrics Testing Page (/test)

**Feature**: `007-lyrics-test-page`  
**Date**: 2026-11-21  

---

## 1. Prerequisites

- Python environment with Flask, MoviePy, and Whisper installed.
- Gemini API key configured in `.env` (`GEMINI_API_KEY`).
- Valid video folder with sample `.mp4` music clips (e.g. `Videos/Video music`).

---

## 2. Validation Scenarios

### Scenario 1: Page Navigation & Streamlined Setup
1. Start application via `python app.py`.
2. Open browser and navigate to `http://127.0.0.1:5000/test`.
3. **Verify**:
   - Navigation bar highlights "Test Lyrics" and provides links to `Auto Render` and `Quản Lý Video`.
   - Setup bar displays only "Thư mục Video nguồn" with existing directory pre-loaded from `config.json`.
   - Image folder input is not shown.

### Scenario 2: Video Scanning & Queue Population
1. Click "Quét Video".
2. **Verify**:
   - Table populates with video items displaying filename, duration, size, and initial status `Chờ test`.
   - Header summary shows total items and pending count.

### Scenario 3: Single-Item Lyrics Testing
1. Click "Test Lyrics" on any video item in the queue.
2. **Verify**:
   - Row transitions to `Đang xử lý` with spinner animation.
   - Within 5–12 seconds, row transitions to `Hoàn thành` displaying detected song title and badge (`Có lyrics (AI)` or `Lời gốc (Original)`).
   - Click "Xem Lyrics" button: inspection modal opens with two side-by-side columns (Raw Whisper vs AI Refined).
   - Test "Copy Lời Gốc" and "Copy Lời AI" buttons.
   - Verify no new MP4 file was added to `outputs/` or `outputs-no-lyrics/`.

### Scenario 4: Batch Queue Lyrics Testing
1. Click "Bắt Đầu Test Tất Cả" in the header actions.
2. **Verify**:
   - The queue sequentially processes each video from top to bottom.
   - Clicking "Dừng Lại" pauses processing after the current active item completes.
   - Processed items retain their lyrics results.

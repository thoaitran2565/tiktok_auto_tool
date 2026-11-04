# Quickstart & Verification Guide: Granular Render Progress & Prediction

**Feature**: Granular Render Progress Tracking and Predictive Estimation  
**Branch**: `001-render-progress-prediction`  
**Date**: 2026-11-04  

---

## Prerequisites

1. Python 3.8+ installed with environment activated.
2. Required packages installed:
   ```bash
   pip install flask moviepy pillow numpy openai-whisper google-genai python-dotenv
   ```
3. FFmpeg installed and available on system `PATH`.
4. Sample test media:
   - At least 1-2 source videos in a folder (e.g., `Videos/` or test directory).
   - At least 1-2 images in an image folder.

---

## Verification Scenarios

### Scenario 1: Initial Cold-Start & Queue Predictions
**Goal**: Verify that queuing videos computes baseline duration predictions before any render runs.

1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Navigate to `http://127.0.0.1:5000/`.
3. Provide folder paths for Images and Videos, then click **"Quét Thư Mục & Tạo Hàng Đợi"**.
4. **Expected Result**:
   - Each item in the queue table displays an estimated completion time (e.g., `~35s`).
   - The toolbar displays an overall batch estimated time (e.g., `Tổng ước tính: ~2m 15s`).
   - A cold-start badge/hint indicates provisional estimates based on source video length.

---

### Scenario 2: Real-Time Granular Progress & Row Expansion (P1)
**Goal**: Verify live stage transitions and the compact expandable UI.

1. Click **"Bắt Đầu Render Tự Động"** or trigger render on a single item.
2. Observe the active queue row:
   - The status badge changes to an active stage with spinner:
     1. `Trích xuất âm thanh`
     2. `Nhận diện giọng nói (Whisper)`
     3. `Làm sạch lời bài hát AI`
     4. `Tạo hình ảnh & lyrics trong suốt`
     5. `Ghép video & mã hóa MP4`
     6. `Xác thực & dọn dẹp`
3. Click the status badge or table row:
   - The row expands inline to reveal a multi-step timeline showing all 6 stages with live elapsed times and checks for completed stages.
4. Observe the progress bar and countdown:
   - The progress bar reflects real progress across stages rather than arbitrary random percentage increments.
   - Remaining time ticks down dynamically based on active elapsed time.
5. **Expected Result**:
   - Transitions occur sequentially with latency under 500ms.
   - Upon finish, status switches to `Hoàn thành` (100%), source is cleaned up safely, and final video player appears.

---

### Scenario 3: Telemetry Collection & Persistence (P2)
**Goal**: Verify that telemetry metrics are stored across app restarts.

1. Complete a render of at least one video.
2. Verify telemetry API response:
   ```bash
   curl http://127.0.0.1:5000/api/render-telemetry
   ```
3. Check that `data/render_telemetry.json` exists on disk and contains:
   - `input_duration_s`, `input_size_mb`, `stage_durations`, `api_latency_ms`, and `total_duration_s`.
4. Restart the Flask app and reload `http://127.0.0.1:5000/api/render-telemetry`:
   - Historical records persist without data loss.

---

### Scenario 4: Dynamic Prediction Accuracy Refinement (P3)
**Goal**: Verify that historical telemetry refines duration predictions on subsequent runs.

1. Render 3-5 consecutive videos.
2. Queue a new video of known length:
   - Observe that `estimated_total_s` now uses empirical device ratios rather than the cold-start fallback.
   - The predicted time closely mirrors previous actual durations for similar length videos within ±25%.


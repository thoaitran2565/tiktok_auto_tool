# Quickstart Validation Guide: Render Speed Optimization

**Feature**: `006-render-speed-optimization`  
**Date**: 2026-11-09  

---

## 1. Prerequisites

- Python 3.8+ with Pillow, MoviePy, and Whisper installed.
- Host FFmpeg with hardware acceleration support (`h264_qsv` or `h264_mf`) and `libx264`.
- Valid test input video and images configured in `config.json`.

---

## 2. Validation Scenarios

### Scenario 1: Media Encoding Speedup (Stage 5)
1. Start application via `python app.py` and navigate to `http://127.0.0.1:5000/`.
2. Load sample videos and trigger single render on Video #1.
3. Observe Stage 5 (`media_encoding`) on the progress timeline.
   - **Expected Outcome**: Stage 5 completes in **under 15–20 seconds** (down from ~130 seconds baseline), showing a 5x–10x speedup.
   - Output video in `outputs/` plays smoothly at exact 1080x1920 vertical resolution with audio synchronized.

### Scenario 2: In-Memory Whisper Caching (Stage 2)
1. Render Video #1: Notice first-time Whisper model load (~15-20s).
2. Render Video #2: Notice Whisper model is already warm in memory.
   - **Expected Outcome**: Stage 2 on Video #2 completes in **under 8 seconds** without reading model weights from disk.

### Scenario 3: AI Lyric Refinement Timeout Protection (Stage 3)
1. Simulate network disconnect or slow API response.
2. Render a video clip.
   - **Expected Outcome**: Stage 3 terminates after 15 seconds maximum and cleanly falls back to raw Whisper transcript, continuing directly to video encoding without stalling the queue.

### Scenario 4: Batch Render Pipelining
1. Queue 3 videos and click "Bắt Đầu Render".
2. Monitor terminal logs and frontend timeline.
   - **Expected Outcome**: While Video #1 is encoding in Stage 5, Video #2 concurrently executes Audio Extraction (Stage 1), Whisper Transcription (Stage 2), and Lyric Refinement (Stage 3).
   - Once Video #1 finishes, Video #2 immediately begins encoding without idle gap.
   - Total batch completion time drops by $> 30\%$.

### Scenario 5: Visual Quality & Constitution Compliance
1. Inspect exported MP4 files in media player:
   - Resolution: Exactly `1080x1920`.
   - Text overlay: Lyrics bounded within 90% vertical safe margins, clean stroke borders, 20% background dimming.
   - Logo: Placed cleanly in upper-right corner.
   - Audio: Clean AAC encoding, zero truncation.


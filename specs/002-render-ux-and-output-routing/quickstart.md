# Quickstart & Verification Guide: Render UX & Output Routing

**Feature**: Render UX Optimizations, Adaptive Queue Learning, and Output Routing  
**Branch**: `002-render-ux-and-output-routing`  
**Date**: 2026-11-04  

---

## Verification Scenarios

### Scenario 1: 100vh Viewport Layout & Sticky Controls
1. Launch the web application: `python app.py`
2. Open `http://127.0.0.1:5000/`.
3. Verify that the window itself has no vertical scrollbar (fits in `100vh`).
4. Scan folders containing 10+ videos.
5. **Expected Result**:
   - The Start, Stop, and Reload buttons are fixed in the top header.
   - Only the table container scrolls internally.
   - Columns are cleanly aligned with balanced spacing.

---

### Scenario 2: Active Render Auto-Scroll & Stage Expansion
1. Click **"Bắt Đầu Render Tự Động"**.
2. **Expected Result**:
   - The actively rendering item immediately scrolls to the top of the table.
   - Its 6-stage accordion timeline automatically opens, displaying real-time step status.
   - As rendering finishes and moves to the next video, the next video smoothly scrolls to the top and opens its timeline.

---

### Scenario 3: Integer Seconds & Progress Plateauing
1. Observe the live timer during rendering.
2. **Expected Result**:
   - All counters show integer seconds (e.g., `Đã qua: 12s • Còn lại: ~38s`).
   - If a stage takes longer than predicted, the progress bar pauses at that stage's ceiling without jumping erratically, advancing to 100% only upon finish.

---

### Scenario 4: Real-Time Dynamic Queue Re-Estimation
1. Observe the estimated duration badge of subsequent videos and the batch total ETA.
2. Wait for Video #1 to complete.
3. **Expected Result**:
   - Video #2 and all subsequent queued items immediately update their estimated times using the newly trained ratio.
   - The total queue ETA badge updates dynamically.

---

### Scenario 5: No-Lyrics Output Routing
1. Render a video without vocals/lyrics or where AI cannot find lyrics.
2. **Expected Result**:
   - The file is saved inside `outputs-no-lyrics/`.
   - The queue row displays a yellow/amber badge: `🔇 Không lời`.
   - The preview and download links reference `/outputs-no-lyrics/...`.

---

### Scenario 6: Modal Lightbox Media Inspection
1. Click on any source image thumbnail or rendered output video.
2. **Expected Result**:
   - A centered Modal overlay opens on a dark blurred backdrop showing the full visual.
   - Clicking the `X` button or clicking the dark background area closes the modal immediately.

---

### Scenario 7: Clean Terminal Logging
1. Look at the terminal running `app.py`.
2. **Expected Result**:
   - The terminal shows concise single-line logs with emoji markers:
     `[1/6] 🎵 Trích xuất âm thanh...`
     `[3/6] ✨ Gemini AI làm sạch lyrics: "..."`
     `[6/6] ✅ Hoàn tất: video.mp4 -> outputs/...`
   - No multiline raw transcript text dumps appear in the terminal.


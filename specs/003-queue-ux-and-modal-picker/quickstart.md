# Quickstart & Verification Guide: Queue UX, Modal Picker & Real-Duration Prediction

**Feature**: Queue UX Refinements, Modal Image Picker, and Real-Duration Prediction  
**Branch**: `003-queue-ux-and-modal-picker`  
**Date**: 2026-11-04  

---

## Verification Scenarios

### Scenario 1: Setup Section Auto-compact & Re-expansion
1. Launch application: `python app.py`.
2. Input folder paths and click **"Quét Thư Mục"**.
3. **Expected Result**:
   - The large 2-input form smoothly collapses into a single-line summary bar (`📁 Ảnh: X tệp • 🎬 Video: Y tệp`).
   - Clicking **"Đổi thư mục"** expands the inputs again.

---

### Scenario 2: Precise Auto-Scroll with Sticky Header Clearance
1. Load a queue containing 10+ video files.
2. Click **"Bắt Đầu Render"**.
3. **Expected Result**:
   - The active rendering row scrolls smoothly to the top of the scrollable table area.
   - The row is aligned flush underneath the sticky header (`<th>`) without any portion being covered or cut off.

---

### Scenario 3: Completed Video Row Locking
1. Allow Video #1 to finish rendering.
2. **Expected Result**:
   - The "Hiện video" button on Row #1 disappears or is disabled.
   - Clicking the image thumbnail on Row #1 is disabled (cursor default, no edit modal opens).
   - Only the finished video preview and download actions in Column 4 remain active.

---

### Scenario 4: Real-Duration Prediction Accuracy
1. Scan a folder containing videos with distinct durations (e.g., 10s clip vs 60s clip).
2. **Expected Result**:
   - The 10s video shows an estimated duration significantly lower (e.g. ~18s - 22s).
   - The 60s video shows an estimated duration proportionally higher (e.g. ~75s - 90s).
   - No items default blindly to the identical ~45s estimate.

---

### Scenario 5: Streamlined Column 1
1. Inspect the "Video Nguồn" column in the queue table.
2. **Expected Result**:
   - No lengthy filename strings are shown.
   - Column cleanly shows item number (e.g. `#1`), ETA badge, and "Hiện video" button.

---

### Scenario 6: Modal Image Picker with Random & Carousel Preview
1. Click the image thumbnail of an unrendered item in Column 2.
2. **Expected Result**:
   - Modal lightbox opens showing the current image in high resolution.
   - Bottom shows a horizontal scrolling carousel of thumbnails from the image folder.
   - Clicking another thumbnail updates the main preview instantly.
   - Clicking **"Chọn ngẫu nhiên"** selects another random image from the folder and updates the main preview.
   - Clicking **"Xác nhận đổi ảnh"** updates the queue item and changes the thumbnail in the table.

---

### Scenario 7: Non-Destructive Queue Refresh Mid-Render
1. While batch rendering is running, click **"Làm Mới"**.
2. **Expected Result**:
   - The browser window does NOT reload.
   - Active render continues without interruption.
   - Any new video added to the folder is appended to the bottom of the table.
   - View remains focused on the currently rendering row.

---

### Scenario 8: Step 6 Timeline Checkmark Completion
1. Observe a video reaching completion.
2. **Expected Result**:
   - In the expanded 6-step accordion, all 6 steps—including Step 6 (Xác thực & dọn dẹp)—display green checkmark icons.
   - No completed video remains with only 5 checkmarks.


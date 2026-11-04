# Research & Technical Decisions: Queue UX, Modal Picker & Real-Duration Prediction

**Feature**: Queue UX Refinements, Modal Image Picker, and Real-Duration Prediction  
**Branch**: `003-queue-ux-and-modal-picker`  
**Date**: 2026-11-04  

---

## 1. Precise Auto-Scroll with Sticky Header Offset

### Decision
Calculate container scroll position explicitly using `tableContainer.scrollTop = targetRow.offsetTop - headerOffset` (or configuring CSS `scroll-margin-top: 44px` on `<tr>` elements before invoking `scrollIntoView({ behavior: 'smooth', block: 'nearest' })`).

### Rationale
- `row.scrollIntoView({ block: 'start' })` aligns the element with the container's top boundary. Because the table header (`<th>`) has `position: sticky; top: 0`, it was overlapping the top 40px of the actively rendering row.
- Explicitly offsetting by `headerOffset` (~42px) ensures the active row sits directly and cleanly below the header with 0px overlap.

---

## 2. Completed Video Row Immutability & Control Locking

### Decision
When an item's status transitions to "Hoàn thành" (or when loaded with "Hoàn thành" status):
1. Hide or disable the "Hiện video" source video toggle.
2. Disable the click handler on the sample image thumbnail (`pointer-events: none; opacity: 0.85; title: "Video đã render xong, không thể đổi ảnh"`).
3. The only active controls in the row become the finished video preview modal and download links in Column 4.

### Rationale
- Modifying the source image after a video has already been rendered with that image is illogical and leads to inconsistent state.
- Locking completed rows reduces visual clutter and prevents accidental user clicks.

---

## 3. Auto-Compacting Folder Setup Section

### Decision
Once `/api/load-folders` returns successfully with items:
1. Automatically collapse `#setupSection` into `#setupCompactBar` displaying:
   `📁 Thư mục ảnh: ${imageCount} ảnh • 🎬 Thư mục video: ${videoCount} video`
2. Provide a compact button `<button class="btn btn-sm btn-secondary" onclick="toggleSetupSection()">Đổi thư mục</button>`.
3. Clicking "Đổi thư mục" smoothly toggles the full input form back open.

### Rationale
- The 2 full-width input fields and large scan button consume ~140px of vertical space, pushing table rows off-screen.
- Compacting it to a 34px bar frees up over 100px of vertical height for the queue table, fulfilling SC-002 (reducing occupied space by >65%).

---

## 4. Real-Duration Prediction Model vs Hardcoded 30s

### Decision
1. **Probe Real Video Duration**: In `app.py` during `/api/load-folders`, probe the real duration of each video file using `VideoFileClip(vid_path).duration` (cached in memory and stored in `session_data['queue']`). If probing fails or file is corrupt, fall back safely to 30.0s.
2. **Dynamic Calibration Formula**: In `services/telemetry_manager.py`:
   - Baseline initialization overhead: `fixed_overhead = 8.0` seconds (Whisper model inference setup + Gemini API network roundtrip).
   - Scaling duration ratio: `render_rate = avg_duration_ratio` (calibrated from telemetry: ~1.1x - 1.4x video length).
   - `predicted_duration = fixed_overhead + (actual_duration_s * render_rate) + (file_size_mb * 0.02)`.
3. Replace hardcoded `30.0` in `app.py` (`/api/render-predictions` and `/api/render-single`) with `item.get('duration_s', 30.0)`.

### Rationale
- Previously, a 10s clip and a 120s clip both received duration predictions calculated as if they were 30s.
- Incorporating actual video duration immediately reduces estimation error by >50% (SC-004).

---

## 5. Streamlined Source Video Column

### Decision
In `queueTable` Column 1 ("Video Nguồn"):
- Remove the text `${item.video_name}`.
- Display:
  - Row order badge (e.g. `#1`, `#2`)
  - Estimated duration badge (`<span class="eta-badge"><i class="fa-regular fa-clock"></i> ~45s</span>`)
  - "Hiện video" toggle button (for pending items only)
  - Hidden `<video>` player element (opens on toggle)

### Rationale
- Video filenames are frequently long, messy strings with special characters that widen columns and push other content out of alignment.
- Removing filename text keeps Column 1 clean, minimal, and uniformly aligned.

---

## 6. Interactive Modal Image Picker with Horizontal Carousel

### Decision
1. Remove legacy `<select>` tag from Column 2. Column 2 shows only the thumbnail image with a hover indicator "Nhấp để đổi ảnh".
2. In `#mediaModal`:
   - Top: High-resolution preview of the current candidate image.
   - Middle: Action bar with:
     - `🎲 Chọn ngẫu nhiên`: Randomly picks another image from `availableImages`, updates candidate preview.
     - `✅ Xác nhận đổi ảnh`: Calls `/api/update-queue` with the candidate image, updates the table row, and closes modal.
     - `✖️ Hủy / Giữ ảnh cũ`: Reverts to original image and closes modal.
   - Bottom: Horizontal scrolling carousel (`overflow-x: auto; display: flex; gap: 8px;`) rendering thumbnail cards of all available images. Clicking any thumbnail immediately sets it as candidate preview.

### Rationale
- Completely eliminates blind text dropdown selection.
- Allows creators to visually assess how the photo looks in full scale before confirming.

---

## 7. Non-Destructive Queue Refresh (`refreshQueueState`)

### Decision
1. Replace `location.reload()` on `#reloadBtn` with `onclick="refreshQueueState()"`.
2. `refreshQueueState()`:
   - Does NOT reload the browser window.
   - Sends background `POST /api/refresh-queue` (or `/api/load-folders` with current paths).
   - Server preserves running render status and appends any newly detected video files to the end of `session_data['queue']`.
   - Client merges new items into `rawQueueData`, re-renders table rows, and smoothly re-scrolls to the actively rendering item.

### Rationale
- Prevents accidental disruption of active batch rendering jobs.
- Allows creators to drop new video clips into the input folder mid-render and pick them up seamlessly.

---

## 8. Step 6 (Finalization) Timeline Completion Tick

### Decision
When the client receives `{ success: true }` from `/api/render-single`:
1. In `startBatchRender()`, iterate all 6 stage items in `STAGE_DEFS`:
   - Set each `step-${id}-${stage.id}` class to `stage-step step-completed`.
   - Set icon to `<i class="fa-solid fa-check"></i>`.
2. In `services/progress_manager.py`: Ensure `complete_item()` sets all stages to `"completed"` status.

### Rationale
- Fixes the race condition where stopping polling right as step 6 finished prevented the UI from receiving the final stage tick.
- Guarantees 100% of completed videos show all 6 green checkmarks (SC-005).


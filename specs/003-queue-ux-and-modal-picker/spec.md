# Feature Specification: Queue UX Refinements, Modal Image Picker, and Real-Duration Prediction

**Feature Branch**: `003-queue-ux-and-modal-picker`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Chỉnh sửa lại tính năng cuộn video render tiếp theo cho nó nằm lên đầu: hiện tại nó cuộn lên bị lệch lên trên 1 xíu. các video đã render xong rồi thì không bấm hiện video và đổi ảnh được nửa. phần thư mục ảnh nguồn và thư mục video khi đã quét thư muc và hiện ra danh sách rồi thì cho gọn lại hoặc tạm ẩn đi để đỡ chiếm diện tích. Thời gian dự đoán vẫn bị lệch quá nhiều, cần tìm giải pháp thích hợp hơn để dự đoán hiệu quả hơn. Cần làm gọn cột video nguồn lại, không cần hiển thị tên video nguồn. cột ảnh ghép mẫu không cần hiện thẻ select đổi ảnh nửa thay vào đó trong model xem ảnh thêm tính năng đổi ảnh bằng nút ramdon và đổi ảnh thủ công thì cho chọn và xem ảnh đối trước khi xác nhận đổi (cơ chế và ui sao cho dễ thao tác nhất). Kiểm tra lại tiến độ, hiện tại đôi lúc nó hoàn thành nhưng trên ui chỉ thấy đánh dấu tích tới bước 5. Chỉnh sửa nút làm mới sẽ không ảnh hưởng đến tiến trình đang chạy mà chỉ load lại thư mục và vẫn cuộn đến video đang render."

## Clarifications

### Session 2026-11-04
- Q: Giao diện chọn ảnh thủ công trong Modal xem ảnh nên được thiết kế theo hình thức nào để người dùng duyệt và xem trước thuận tiện nhất? (FR-007) → A: Option A — Dải băng chuyền thumbnail (carousel) cuộn ngang nằm ở cạnh dưới của Modal; click ảnh nào thì khung trên lập tức hiển thị ảnh đó ở độ phân giải đầy đủ, có nút "Xác nhận đổi ảnh" và nút "Chọn ngẫu nhiên".
- Q: Khi người dùng bấm nút "Làm Mới" trong lúc tiến trình render đang chạy, nếu phát hiện có thêm video mới trong thư mục, hệ thống nên xử lý hàng đợi như thế nào? (FR-010) → A: Option A — Tự động giữ nguyên trạng thái các video đang render / đã hoàn thành, thêm các video mới phát hiện vào cuối hàng đợi (nếu có) và giữ góc nhìn cuộn bám theo video đang chạy.
- Q: Khi đã quét thư mục xong và bảng hàng đợi hiển thị, thanh thu gọn thư mục (Setup Section) nên hiển thị thông tin gì và tương tác thế nào khi người dùng muốn đổi thư mục? (FR-002) → A: Option A — Thu gọn thành 1 thanh tóm tắt siêu nhỏ gồm icon + số lượng tệp đã quét (ví dụ: "📁 Ảnh: 12 tệp • 🎬 Video: 8 tệp") kèm nút "Đổi thư mục"; bấm vào sẽ bung lại 2 ô nhập đường dẫn và nút quét như ban đầu.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seamless Queue Interaction & Viewport Optimization (Priority: P1) 🎯 MVP

As a creator managing a large batch rendering queue, I want the folder setup section to auto-compact upon scanning, the source video column to remain streamlined without filename clutter, the active rendering row to align accurately directly beneath the sticky table header without clipping, and completed video rows to be permanently locked against unintended image changes or playback toggles.

**Why this priority**: When rendering 20-50 videos, screen real estate and rock-solid queue navigation are critical. Eliminating header clipping, hiding completed controls, and compacting setup inputs maximizes table visibility and eliminates operator confusion.

**Independent Test**: Scan a folder with 10+ videos. Verify that the setup panel collapses into a compact bar, the video source column only displays the ETA badge and preview toggle without text filenames, and when batch rendering starts, each active row scrolls directly flush below the sticky table header. Once an item is finished, verify its image edit and video preview toggles are disabled/locked.

**Acceptance Scenarios**:

1. **Given** folders have been scanned and the queue is populated, **When** the table appears, **Then** the folder input form auto-compacts into a single-line summary bar showing scanned counts (`📁 Ảnh: X tệp • 🎬 Video: Y tệp`) with a "Đổi thư mục" button to re-expand the inputs if needed.
2. **Given** an active batch render advances to the next video, **When** auto-scrolling triggers, **Then** the row scrolls accurately to the top of the table viewport flush below the sticky table header (`<th>`) without being obscured or offset.
3. **Given** a video item reaches "Hoàn thành", **When** rendered in the table, **Then** its source video preview toggle and image modification controls are disabled/hidden to prevent accidental modifications to finished items.
4. **Given** the queue table renders, **When** viewing the first column ("Video Nguồn"), **Then** it presents clean controls (order number, duration prediction badge, preview button) without displaying verbose filename text.

---

### User Story 2 - Interactive Modal Image Picker with Preview Confirmation (Priority: P2)

As a creator reviewing and curating thumbnails before rendering, I want to click any source image to open a full-resolution inspector modal where I can either roll a "Random" image or manually browse available candidate images with instant preview before confirming the change, replacing clumsy dropdown selects in the table.

**Why this priority**: Choosing matching background images through a plain `<select>` text dropdown with dozens of filenames is slow, error-prone, and blind. A visual modal with quick Random pick and manual preview-before-confirm makes curation effortless.

**Independent Test**: Click an image thumbnail in the queue table. Verify the modal opens without `<select>` dropdowns in the table. Click "Chọn ngẫu nhiên" to swap the image immediately, or select a candidate thumbnail from the gallery picker, inspect it full-size, and click "Xác nhận đổi ảnh" to commit the change.

**Acceptance Scenarios**:

1. **Given** the queue table is displayed, **When** viewing the "Ảnh Ghép Mẫu" column, **Then** the legacy `<select>` dropdown is removed, displaying only the clickable image thumbnail.
2. **Given** a user clicks on an uncompleted item's image thumbnail, **When** the modal inspector opens, **Then** it provides an image curation toolbar containing a "Chọn ngẫu nhiên" (Random) button and a visual candidate selector.
3. **Given** a candidate image is selected in the modal, **When** clicked, **Then** the main modal view immediately displays that candidate in full resolution for inspection with "Xác nhận đổi" and "Hủy" action buttons.
4. **Given** the user confirms the change, **When** the modal closes, **Then** the queue item's image is updated on the server and the table thumbnail immediately reflects the new selection.

---

### User Story 3 - Real-Duration Accurate Predictive Estimation (Priority: P3)

As a user scheduling render batches, I want duration estimates to be computed from the actual duration of each input video rather than a fixed 30-second constant, combining fixed model initialization overhead with duration-scaled processing rates so that predictions are realistic and accurate.

**Why this priority**: Videos in production range from 8 seconds to 3+ minutes. Hardcoding an assumed 30-second duration caused severe estimation errors (up to 300% off for short or long clips).

**Independent Test**: Load videos of differing lengths (e.g. 10s, 45s, 90s). Verify that each item's predicted time reflects its real video duration, and total batch ETA scales accurately with the sum of real video lengths.

**Acceptance Scenarios**:

1. **Given** a folder of videos is scanned, **When** durations are probed, **Then** the actual duration (in seconds) of each source video is measured and cached in the queue item data.
2. **Given** actual duration is known, **When** duration predictions are calculated, **Then** the estimation model applies a calibrated formula: `estimate = fixed_overhead + (actual_duration * duration_ratio)`, replacing the hardcoded 30.0s constant.
3. **Given** telemetry records accumulate from completed jobs, **When** re-estimating, **Then** both the fixed overhead and duration ratios dynamically adjust to reflect actual local machine performance.

---

### User Story 4 - Robust Non-Destructive Refresh & Timeline Finalization Fidelity (Priority: P4)

As a creator monitoring a live render batch, I want the "Làm Mới" (Reload) button to refresh queue status and folder contents without reloading the browser page or terminating the active render, and I want the timeline accordion to reliably check off all 6 steps upon completion without leaving step 6 unticked.

**Why this priority**: Accidentally killing an ongoing 20-video render by clicking "Làm Mới" causes wasted processing time. Furthermore, completed videos showing only 5/6 ticks confuses users as to whether the video actually finalized.

**Independent Test**: Start batch rendering and click "Làm Mới" mid-render. Verify the browser page does not reload, the render continues uninterrupted, and the view re-scrolls to the active row. When rendering completes, verify all 6 steps in the timeline accordion display green checkmarks (`step-completed`).

**Acceptance Scenarios**:

1. **Given** a batch render is currently in progress, **When** the user clicks "Làm Mới", **Then** the client performs a background asynchronous data refresh without refreshing the webpage (`location.reload()`), preserving execution state, appending any newly added videos in the source folder to the end of the queue, and smoothly maintaining scroll focus on the active item.
2. **Given** a video finishes stage 6 (`finalization`), **When** the server returns `success: true`, **Then** the client UI ensures all 6 timeline stages—including Step 6 (Xác thực & dọn dẹp)—are explicitly set to completed status with checkmarks.

---

### Edge Cases

- **Folder Path Changed while Rendering**: If user re-scans folders while a batch is rendering, the system must warn or disable folder rescanning until the active queue finishes or is stopped.
- **Corrupted or Zero-Length Video Probe**: If an input video file cannot be probed for duration (e.g. invalid codec header), the system must gracefully fall back to default estimated duration without failing the folder scan.
- **Single Image in Folder**: If only 1 image exists in the image folder, the "Chọn ngẫu nhiên" button must inform the user that only 1 image is available rather than erroring.
- **Rapid Clicking on Refresh**: Debounce the "Làm Mới" action to prevent spamming background requests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The UI MUST accurately calculate the vertical scroll offset when focusing the active video row, positioning the row flush below the sticky table header without clipping or upward offset.
- **FR-002**: Upon successfully scanning source folders, the setup section MUST automatically collapse into a compact single-line summary bar displaying file counts (`📁 Ảnh: X tệp • 🎬 Video: Y tệp`) with a "Đổi thư mục" toggle button to re-expand the full input form when needed.
- **FR-003**: The table column "Video Nguồn" MUST omit redundant filename text, displaying only the item index, prediction ETA badge, and video preview toggle button.
- **FR-004**: When a video item reaches "Hoàn thành", its preview and editing controls MUST be disabled and locked against accidental alteration.
- **FR-005**: The table column "Ảnh Ghép Mẫu" MUST remove the legacy `<select>` dropdown. Clicking the thumbnail MUST open an image curation modal.
- **FR-006**: The image modal MUST provide a "Chọn ngẫu nhiên" (Random) button that picks an alternative image from the scanned pool and updates the queue item.
- **FR-007**: The image modal MUST provide a horizontal scrolling thumbnail carousel at the bottom of the modal that lets the user preview candidate images in full resolution in the main view above before clicking "Xác nhận đổi" to commit the change.
- **FR-008**: The system MUST probe and cache the actual duration (in seconds) of each source video during folder scanning or prediction generation, eliminating all hardcoded 30.0s assumptions.
- **FR-009**: Duration prediction calculations MUST be derived from actual probed media duration combined with calibrated baseline overhead and scaling ratios.
- **FR-010**: Clicking the "Làm Mới" control MUST execute an asynchronous data sync without reloading the web page, preserving running render tasks, appending any newly detected videos in the folder to the queue, and auto-scrolling to the active rendering row.
- **FR-011**: Upon receiving render completion confirmation, the UI MUST verify and explicitly mark all 6 timeline steps (including Step 6 - `finalization`) as completed with green checkmark indicators.

### Key Entities

- **Probed Video Metadata**: Entity storing `video_name`, `video_path`, actual `duration_s`, and `size_mb`.
- **Image Picker Session State**: Client state tracking `current_image_name`, `candidate_image_name`, `queue_item_id`, and `candidate_preview_url`.
- **Collapsed Setup State**: UI state managing the collapsed vs expanded presentation of folder input controls.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of auto-scrolled active rows align flush within 4px of the bottom edge of the sticky table header with zero obscured content.
- **SC-002**: Screen space occupied by folder setup inputs decreases by at least 65% in the collapsed state.
- **SC-003**: 100% of completed video rows have their editing and source playback controls locked against user mutation.
- **SC-004**: Duration estimation error across videos with non-standard lengths (under 20s or over 60s) is reduced by at least 50% compared to the fixed 30s baseline.
- **SC-005**: 100% of finished videos in the queue exhibit all 6 green checkmarks in their expanded accordion timeline.
- **SC-006**: Clicking "Làm Mới" during an active batch render causes 0 interruptions to the ongoing pipeline.

## Assumptions

- **Duration Probing**: MoviePy `VideoFileClip(path).duration` or lightweight media headers can reliably determine video length within 200ms per file during scan.
- **Image Pool**: The image folder contains at least one valid image file (.jpg, .jpeg, .png, .webp).
- **Sticky Header Height**: The table header height is fixed at ~42px, allowing exact scroll margin calculation.


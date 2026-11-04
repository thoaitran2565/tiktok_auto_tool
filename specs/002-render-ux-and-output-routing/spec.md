# Feature Specification: Render UX Optimizations, Adaptive Queue Learning, and Output Routing

**Feature Branch**: `002-render-ux-and-output-routing`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Bộ đếm thời gian trên ui chỉ hiển thị từng giây thôi. Video đang render thì cuộn nó lên đầu và hiện chi tiết các bước ra. Đảm bảo khi thu thập được càng nhiều dữ liệu thì dự đoán thời gian hoàn thành ngày càng chính xác. Cập nhật thời gian dự đoán mới cho các video mới trong quá trình chạy video tiếp theo luôn và cả thời gian tổng. Cho các nút bên dưới (chạy/dừng lại, làm mới) lên trên header luôn và cho khung chứa dài chi bằng tối đa chiều cao màn hình cho phép để nó không bị cuộn xuống, chỉ cuộn phần danh sách video render thôi. Thanh progess chạy theo thời gian dự đoán và ngắt quảng giữa các bước nếu chậm hơn dự tính trước khi tiến đến 100%.. Thêm thư mục outputs-no-lyrics để điều hướng lưu video không có lyrics từ model ai nào lưu vào đó. Thêm tính năng xem ảnh nguồn và video thành phẩm. Sắp xếp lại bố cục ui cho thẳng hàng và đồng đều hơn. Giảm bớt log trong terminal khi chạy tool, cho log dễ nhìn hơn."

## Clarifications

### Session 2026-11-04
- Q: Tính năng xem trước ảnh nguồn và video thành phẩm nên được hiển thị theo hình thức nào trên giao diện? → A: Cửa sổ Modal / Lightbox phóng to nổi giữa màn hình với nền mờ tối, đóng nhanh khi bấm nút đóng hoặc nhấp vào vùng tối xung quanh.
- Q: Video khi được phân loại vào thư mục `outputs-no-lyrics` nên được đánh dấu và hiển thị như thế nào trên giao diện và trang quản lý? → A: Option A — Gắn nhãn badge phân loại "Có lyrics" (xanh ngọc) hoặc "Không lời" (vàng nhạt) cạnh tên video thành phẩm và lưu cờ `has_lyrics: true/false` vào `videos_db.json`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Viewport-Constrained Layout & Active Render Auto-Focus (Priority: P1)

As a content creator running batch render jobs, I want the web interface to fit neatly inside my browser window with action controls anchored in the header, and I want the currently rendering video to automatically scroll to the top of the queue with its step-by-step progress expanded, so that I can monitor the active process at a glance without having to scroll the entire web page up and down.

**Why this priority**: During long batch runs, users frequently lose track of the actively processing video when the list exceeds screen height. An anchor layout with automatic scrolling and expanding keeps operational focus immediate and prevents UI layout awkwardness.

**Independent Test**: Load a queue with 10+ videos, start batch rendering, and observe that the window itself does not scroll; only the table scrolls internally, the action buttons remain fixed at the top, and the active video automatically scrolls into view with its 6-stage timeline expanded.

**Acceptance Scenarios**:

1. **Given** a batch render queue with more items than can fit on screen, **When** the page renders, **Then** the main container height is constrained to the viewport height (`100vh`) with fixed header controls (Start, Stop, Reload) and an independently scrollable table.
2. **Given** a batch render is progressing from one video to the next, **When** a video begins rendering, **Then** the interface automatically scrolls that row to the top of the table viewport and expands its stage timeline accordion.
3. **Given** multiple rows with varying content lengths, **When** rendered, **Then** table columns, badges, buttons, and text maintain aligned vertical and horizontal grid baselines.

---

### User Story 2 - Smooth Progress Plateauing & Real-Time Adaptive Re-Estimation (Priority: P2)

As a content creator, I want progress timers displayed in clean integer seconds, with progress bars that smoothly animate according to predicted stage timings but pause at stage boundaries if a stage takes longer than estimated, and I want subsequent video duration estimates to adaptively recalculate in real-time as each video finishes.

**Why this priority**: Progress bars that jump abruptly or count down in fractional milliseconds look twitchy and unpolished. Furthermore, re-evaluating the queue ETA dynamically after every finished video ensures that learning from recent runs improves queue scheduling accuracy immediately.

**Independent Test**: Run a video render and verify that timers display strictly in whole seconds (e.g., `12s`, `~45s`). Observe that the progress bar animates smoothly and plateaus if a stage exceeds estimated time, jumping to 100% only on completion. Verify that queued items and total batch ETA update their predictions right after each video finishes.

**Acceptance Scenarios**:

1. **Given** an active rendering task, **When** progress updates occur, **Then** all elapsed and remaining time displays show rounded whole seconds without decimal fractions.
2. **Given** a stage runs longer than predicted, **When** the elapsed time reaches the predicted stage threshold, **Then** the progress bar pauses (plateaus) at that stage's boundary until the backend confirms stage completion before continuing to the next phase.
3. **Given** a video finishes rendering and adds its telemetry, **When** the next video starts, **Then** all remaining queued items and the batch queue summary immediately recalculate their estimated times using the updated model ratios.

---

### User Story 3 - No-Lyrics Output Routing & Media Inspection (Priority: P3)

As a video creator producing both lyric videos and instrumental/speechless short clips, I want videos that contain no AI-detected lyrics to be saved automatically into a separate `outputs-no-lyrics` folder, and I want an easy way to view high-resolution previews of source images and finished videos directly in the interface.

**Why this priority**: Creators separate lyric-heavy music clips from ambient/B-roll videos for different channels. Routing speechless videos automatically prevents manual sorting, and rich media inspection saves creators from opening file explorer to check quality.

**Independent Test**: Render one video with lyrics and one video without vocals/lyrics. Verify the lyric video is saved to `outputs/` with a "Có lyrics" badge and the speechless video is saved to `outputs-no-lyrics/` with a "Không lời" badge. Click to preview both source images and rendered output videos in the modal lightbox.

**Acceptance Scenarios**:

1. **Given** a video where Whisper/Gemini finds no lyrics or where lyrics are unavailable, **When** rendering finalizes, **Then** the output video is saved into the `outputs-no-lyrics/` directory, recorded with `has_lyrics: false` in `videos_db.json`, tagged with a "Không lời" badge, and downloadable via the secondary folder route.
2. **Given** a video with verified AI lyrics, **When** rendering finalizes, **Then** the output video is saved into the primary `outputs/` directory, recorded with `has_lyrics: true`, and tagged with a "Có lyrics" badge.
3. **Given** any queue item, **When** clicking a preview action for the source image or output video, **Then** a centered Modal/Lightbox overlay displays the full visual over a dark blurred backdrop, which closes immediately when clicking the close button or clicking the backdrop area.

---

### User Story 4 - Clean Terminal Logging (Priority: P4)

As a developer or creator watching the console terminal, I want clean, concise, formatted log lines without noisy raw transcript blocks or repeated debug spam, so that I can easily monitor tool health in the terminal.

**Why this priority**: Terminal logs currently output large multiline text dumps and model iteration logs that push useful operational status off-screen.

**Independent Test**: Run a render and verify the terminal displays concise, one-line status indicators for each of the 6 stages and suppresses voluminous transcript debug dumps.

**Acceptance Scenarios**:

1. **Given** a video is rendering, **When** stage transitions occur, **Then** the console prints a concise single-line status message with an emoji and stage label.
2. **Given** speech recognition and AI cleansing occur, **When** lyrics are processed, **Then** verbose prompt texts and raw Whisper segments are suppressed from stdout.

---

### Edge Cases

- **Viewport Size Adjustments**: When running on smaller laptop screens (e.g., 768px height), header and summary cards must remain compact so that at least 2 full table rows remain visible within the scrollable viewport.
- **Videos Without Audio or Very Short Clips**: If a video has no audio track, output routing must gracefully record the failure or route to `outputs-no-lyrics/` if fallback video generation is supported.
- **Dynamic Queue Additions / Re-scans**: If folders are rescanned while prior telemetry exists, the initial estimates must immediately reflect the newest trained averages.
- **Missing `outputs-no-lyrics` Directory**: The system must automatically ensure the existence of `outputs-no-lyrics/` on initialization without failing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application layout MUST fit within the viewport height (`100vh`), pinning header navigation, summary metrics, and batch control buttons (Start, Stop, Reload) in a sticky header while allowing only the queue table body to scroll vertically.
- **FR-002**: The UI MUST automatically scroll the actively rendering video row to the top of the table viewport and expand its detailed 6-stage timeline accordion upon starting.
- **FR-003**: All user-facing time counters (elapsed time, remaining countdown, estimated item duration, and batch queue total) MUST be formatted strictly in integer seconds (e.g. `14s`, `~45s`, `1m 20s`), eliminating decimal places.
- **FR-004**: The progress bar MUST interpolate progress smoothly based on predicted stage durations and MUST pause (plateau) at the stage boundary if the active stage exceeds its predicted time, advancing to 100% only upon stage 6 completion.
- **FR-005**: The system MUST automatically recalculate duration predictions for all remaining queued items and update the aggregate queue ETA immediately after each video render completes.
- **FR-006**: The system MUST support an `outputs-no-lyrics/` output directory, automatically created on startup alongside `outputs/`.
- **FR-007**: When a video contains no AI-cleansed lyrics, the final MP4 MUST be saved into `outputs-no-lyrics/` instead of `outputs/`, recorded in `videos_db.json` with attribute `has_lyrics: false`, and tagged on the interface with a distinct 'Không lời' badge.
- **FR-008**: The web interface MUST provide a centered Modal/Lightbox overlay for high-resolution inspection of source images and rendered output videos, featuring a blurred dark backdrop that closes seamlessly when clicking the close button or clicking anywhere on the backdrop.
- **FR-009**: The queue table layout MUST maintain aligned vertical and horizontal grid baselines with consistent column widths, paddings, and badge alignments.
- **FR-010**: Terminal logging MUST be formatted with concise, single-line stage progress messages, suppressing verbose raw lyrics dumps, API prompts, and redundant debug statements.

### Key Entities

- **Queue Viewport Layout**: Configuration defining the fixed header dimensions, sticky control bar, and scrollable table container constrained to viewport height.
- **Output Target Route**: Specification of the target destination directory (`outputs` for AI lyric videos with `has_lyrics: true` vs. `outputs-no-lyrics` for instrumental/speechless videos with `has_lyrics: false`).
- **Interpolated Progress State**: Real-time progress metric tracking stage progress interpolation, stage boundary plateau locks, and integer timing counters.
- **Media Preview Inspector**: Modal or lightbox entity displaying high-resolution previews for source images and rendered MP4 files with backdrop dismiss functionality.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The application interface generates zero outer window scrollbar on viewports with height >= 700px; 100% of scrolling is contained within the queue table body.
- **SC-002**: Upon starting a render, the active queue row scrolls into view and expands its timeline within 200ms.
- **SC-003**: 100% of displayed time values on the interface use whole integer seconds with zero decimal places.
- **SC-004**: 100% of videos produced without AI lyrics are routed into `outputs-no-lyrics/`, with zero misplaced in `outputs/`.
- **SC-005**: Terminal log volume during a standard video render is reduced by at least 60% in line count, producing clean, single-line progress updates.

## Assumptions

- **Browser Viewport Standards**: Standard desktop displays with at least 1280x720 resolution.
- **No-Lyrics Classification**: A video is classified as "no lyrics" if `lyric_source != "AI"` or if the cleaned lyrics string is empty or contains no valid song verses.
- **Web Server Route for Secondary Output**: The Flask server will expose `/outputs-no-lyrics/<filename>` and adjust download endpoints accordingly.
- **Integer Formatting**: Any time less than 60 seconds is displayed as `Xs`, and times >= 60 seconds are displayed as `Xm Ys`.

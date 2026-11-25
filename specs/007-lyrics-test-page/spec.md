# Feature Specification: Lyrics Testing Page (/test)

**Feature Branch**: `007-lyrics-test-page`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Tạo ra trang dùng để test với đường dẫn /test. Về giao diện tương tự như trang chính nhưng chỉ xử lý lyrics của video để xem kết quả, không cần xuất video"

## Clarifications

### Session 2026-11-21
- Q1 (Folder Configuration Scope): Option A — Chỉ cần thư mục Video. Thanh setup trên `/test` tinh gọn, loại bỏ ô chọn thư mục Ảnh để tập trung tối đa vào kiểm thử âm thanh và lyrics.
- Q2 (Lyrics Result Display Format): Option A — Hiển thị tóm tắt trên dòng bảng (trạng thái, câu đầu, huy hiệu nguồn) kèm nút "Xem Lyrics" mở modal đối chiếu 2 cột song song (Lời gốc Whisper vs Lời AI hoàn chỉnh) có nút Copy.
- Q3 (Batch Queue Testing Scope): Option A — Hỗ trợ đầy đủ cả 2 chế độ: Test từng video đơn lẻ (nút ở từng dòng) và Test hàng loạt tự động tuần tự ("Bắt Đầu Test Tất Cả" kèm nút "Dừng Lại" ở thanh điều khiển).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dedicated Lyrics Testing Interface at /test (Priority: P1)

As a content creator or tester, I want to access a dedicated testing page at route `/test` that looks and feels like the main interface, so that I can quickly inspect audio transcription and AI lyrics cleansing without having to render full MP4 videos.

**Why this priority**: Testing lyrics recognition and AI refinement currently requires running the full 6-stage video rendering pipeline. By decoupling lyrics testing from media encoding, creators can verify lyrics quality, spelling, and AI refinement within seconds per video instead of minutes.

**Independent Test**: Navigate to `http://127.0.0.1:5000/test`. Load videos from the configured video directory, click "Kiểm Tra Lyrics" on any video, and view the extracted lyrics and AI refinement result in real time without creating or exporting any MP4 video.

**Acceptance Scenarios**:

1. **Given** a user navigates to `/test`, **When** the page loads, **Then** it renders a familiar interface styled consistently with the main application, displaying folder scanning controls and a video queue table.
2. **Given** a video folder with media files, **When** the user scans the folder, **Then** the queue populates with source videos displaying duration, file size, and testing status (`Chờ test`, `Đang xử lý`, `Hoàn thành`, `Lỗi`).
3. **Given** a queued video, **When** the user triggers a single lyrics test, **Then** the system extracts audio, runs Whisper speech recognition, and refines the text with AI without triggering visual canvas generation or FFmpeg media encoding.

---

### User Story 2 - Side-by-Side Lyrics Comparison & Inspection (Priority: P1)

As a creator, I want to easily compare the raw Whisper transcript against the AI-refined lyrics along with detected title and source indicator, so that I can evaluate AI cleaning accuracy, identify missed lyrics, or verify song identification.

**Why this priority**: Creators need transparent diagnostic visibility into what Whisper actually heard versus what Gemini AI altered or identified.

**Independent Test**: Run a lyrics test on a video clip. Open the lyrics result view. Verify that raw transcript, AI-cleaned text, source badge (`AI` vs `Original`), and the first-line title are clearly displayed side-by-side or in structured tabs with copy-to-clipboard functionality.

**Acceptance Scenarios**:

1. **Given** a completed lyrics test on an item, **When** viewing the result, **Then** the interface displays both the raw Whisper text and the AI-refined lyrics with distinct formatting.
2. **Given** an AI refinement that identified a known song, **When** inspecting the result, **Then** a badge indicates `AI` as the source along with the generated title.
3. **Given** an AI fallback due to timeout or missing lyrics, **When** inspecting the result, **Then** the interface displays `Original` source badge and shows the clean raw text.

---

### User Story 3 - Batch Lyrics Testing across Queue (Priority: P2)

As a creator with 20+ videos, I want to batch test all videos in the queue automatically, so that I can review transcription quality across an entire batch in one continuous run before deciding which videos to render.

**Why this priority**: Allows rapid verification of an entire folder in 1–2 minutes instead of 30+ minutes of video rendering.

**Independent Test**: Queue 5 videos on `/test` and click "Test Tất Cả". Observe sequential execution with live progress indicators. Verify all 5 items display final lyrics status upon completion.

**Acceptance Scenarios**:

1. **Given** multiple queued videos, **When** clicking "Bắt Đầu Test", **Then** the system sequentially processes each item's lyrics with live percentage and stage progress indicators.
2. **Given** a batch test in progress, **When** clicking "Dừng Lại", **Then** processing cleanly pauses after the current item without corruption.

---

### Edge Cases

- **Video has no audio track**: The system MUST detect missing audio early and mark the item as `Lỗi: Video không có âm thanh` without crashing the queue.
- **Whisper transcription produces empty text (instrumental music)**: The system MUST display `[Không nhận diện được giọng hát/lời]` and mark source as `None` or `Không lời`.
- **Gemini AI timeout or rate limit during test**: The system MUST enforce the 15-second timeout and immediately display the raw Whisper transcript marked with `Original` fallback badge.
- **Large lyrics text exceeding view bounds**: The results view MUST provide scrollable containers and responsive typography to prevent layout breakage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST serve a dedicated lyrics testing web page at route `/test` using a layout and styling consistent with `index.html`.
- **FR-002**: The `/test` page MUST provide a streamlined setup toolbar requiring only the video folder path, automatically loading existing configuration from `config.json` while omitting the image folder input.
- **FR-003**: The system MUST provide an isolated API endpoint (e.g. `/api/test-lyrics`) that executes only audio extraction, speech transcription (Whisper), and AI refinement (Gemini) without executing visual compositing or FFmpeg encoding.
- **FR-004**: The system MUST display a lyrics summary on each table row (status badge, source badge `AI` / `Original`, first-line title) and provide a "Xem Lyrics" modal presenting side-by-side comparison of raw Whisper transcript and AI-refined lyrics with one-click copy to clipboard.
- **FR-005**: The system MUST support both single-item test execution via row-level action buttons and batch queue test execution via global "Bắt Đầu Test" / "Dừng Lại" header action controls with live progress tracking.
- **FR-006**: The `/test` interface MUST reuse the existing warm in-memory `TranscriptionService` singleton to ensure fast sub-8-second transcription per video.
- **FR-007**: The system MUST NOT generate or write final MP4 video files into `outputs/` or `outputs-no-lyrics/` during `/test` runs, and MUST clean up any intermediate temporary audio clips upon test completion.
- **FR-008**: The interface MUST provide a quick-action button or navigation link to switch between the main rendering page (`/`), the test page (`/test`), and video management (`/manage`).

### Key Entities

- **LyricsTestItem**:
  - `id`: Unique identifier in test queue.
  - `video_name`: Name of source video file.
  - `video_path`: Absolute path to video.
  - `duration_s`: Duration of audio in seconds.
  - `status`: Execution state (`Chờ test`, `Đang xử lý`, `Hoàn thành`, `Lỗi`).
  - `raw_lyrics`: Unprocessed text from Whisper recognition.
  - `refined_lyrics`: Cleaned/identified lyrics from Gemini AI.
  - `lyric_source`: Source identifier (`AI`, `Original`, `None`).
  - `first_line`: Short title extracted from lyrics.
  - `error_message`: Error detail if failed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Creators can complete lyrics extraction and AI review for a 30s video in under **10–12 seconds** on `/test` (compared to 25–40s for full video render).
- **SC-002**: **0 MB** of MP4 video files are written to disk during testing on `/test`.
- **SC-003**: 100% of tested items clearly expose both raw transcript and AI-cleaned lyrics with source attribution.
- **SC-004**: Users can seamlessly switch between `/`, `/test`, and `/manage` with a single click from the top navigation bar.

## Assumptions

- Source videos are in MP4, MKV, AVI, or MOV format containing valid audio streams.
- The existing in-memory Whisper model and Gemini API configuration from `.env` are shared with `/test`.
- Temporary scratch audio files created for transcription are purged immediately after test completion.

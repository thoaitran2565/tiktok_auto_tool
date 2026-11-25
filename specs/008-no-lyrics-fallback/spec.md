# Feature Specification: No-Lyrics Fallback & Chill Video Naming

**Feature Branch**: `008-no-lyrics-fallback`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Với video không trích xuất được lyric thì bỏ qua bước tạo lyric trên video, tên video đặt là "Cuộc sống chill [timestamp]""

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Video Rendering Without Lyric Overlay (Priority: P1) 🎯 MVP

When a user processes a video whose audio does not contain recognizable song lyrics (e.g., instrumental background music, sound effects, ambient speech, or speech where AI determines no lyrics exist), the system automatically skips the lyric text image generation and overlay compositing steps. The final output video is cleanly rendered with the background visual (single image or multi-image slideshow), logo watermark, and original audio, without any text superimposed on the canvas.

**Why this priority**: Essential to prevent garbled text, AI explanatory disclaimers, or noise transcripts from being burned into the video. Delivers immediate value by producing clean aesthetic videos for non-lyric audio.

**Independent Test**: Provide an instrumental or speech-free video. Run render pipeline. Verify generated video contains the background image and original audio, but completely omits any lyrics text on the video frame.

**Acceptance Scenarios**:

1. **Given** a source video with instrumental music or unrecognizable lyrics, **When** the render pipeline processes the video, **Then** it skips lyric image creation and produces a video frame containing only the background visual and logo watermark.
2. **Given** a video without lyrics, **When** rendering completes, **Then** the audio from the original video is preserved with 100% fidelity.

---

### User Story 2 - Standardized "Cuộc sống chill" Naming Convention (Priority: P1)

When a video has no extractable lyrics, instead of using arbitrary Whisper text fragments, hallucinated words, or AI disclaimer messages as the file name, the system names the rendered video file using the standardized format `"Cuộc sống chill [timestamp].mp4"`.

**Why this priority**: Ensures clean, consistent, and recognizable file names for social media publishing without ugly or nonsensical titles (e.g. avoiding filenames like `(Không có nội dung lời bài hát).mp4`).

**Independent Test**: Render a non-lyric video and check the output directory. Verify the resulting file name starts with `Cuộc sống chill ` followed by the formatted timestamp and `.mp4` extension.

**Acceptance Scenarios**:

1. **Given** a video where no lyrics are detected, **When** rendering finishes, **Then** the output file is saved as `"Cuộc sống chill [timestamp].mp4"`.
2. **Given** multiple non-lyric videos rendered consecutively, **When** each finishes, **Then** each receives a unique timestamp-based filename preventing file overwrite collisions.

---

### User Story 3 - Intelligent Non-Lyric Audio Detection & Queue Classification (Priority: P2)

The system accurately determines whether audio contains authentic lyrics or should be classified as "No Lyrics". It detects cases such as empty Whisper transcripts, AI disclaimers (e.g., "Đoạn âm thanh không chứa lời bài hát..."), channel subscribe advertisements, and pure instrumental sounds, classifying them as `has_lyrics: false` and updating queue/database status badges accordingly.

**Why this priority**: Prevents AI conversational replies or prompt regurgitations from accidentally being treated as valid song lyrics.

**Independent Test**: Test with audio containing an AI refusal/disclaimer text. Verify system flags item as `has_lyrics: false` and invokes the chill fallback workflow.

**Acceptance Scenarios**:

1. **Given** an audio clip where Whisper produces empty text or silence, **When** lyrics analysis runs, **Then** it immediately flags the item as non-lyric and bypasses AI text cleanup.
2. **Given** an audio clip where AI indicates no song lyrics exist, **When** lyrics analysis evaluates the response, **Then** it marks `has_lyrics: false` and sets the title to `"Cuộc sống chill [timestamp]"`.

---

### Edge Cases

- **Pure instrumental / ambient music**: Whisper produces empty string or musical notes (e.g., `♪♪♪`). System must detect this as no lyrics.
- **Speech ads / channel intros without music lyrics**: Whisper transcribes "Hãy like và subscribe kênh...". AI cleansing detects no song lyrics; system must treat as no lyrics rather than putting intro speech as lyrics.
- **Gemini API timeout or network failure on non-lyric video**: When AI times out, if raw Whisper text is non-lyric or empty, fallback must still trigger the "Cuộc sống chill" flow without lyrics overlay.
- **Rapid batch rendering collision**: Multiple videos finishing within the same second must append a sub-second suffix or unique identifier to `[timestamp]` to prevent file collision.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST identify audio as non-lyric when Whisper transcription is empty, contains only noise symbols, or when AI processing determines no valid song lyrics exist.
- **FR-002**: System MUST bypass lyric image generation (`create_lyrics_image_pil`) and overlay pasting on canvas when a video is identified as having no lyrics.
- **FR-003**: System MUST name exported non-lyric videos using the format `"Cuộc sống chill [timestamp].mp4"`.
- **FR-004**: System MUST format `[timestamp]` as a Unix timestamp (e.g., `Cuộc sống chill 1732168137.mp4`), appending a sub-second suffix if a filename collision occurs.
- **FR-005**: System MUST route rendered non-lyric video files to the dedicated `outputs-no-lyrics/` directory, preserving separation from lyric-enabled videos in `outputs/`.
- **FR-006**: System MUST update the video queue and database record (`videos_db.json`) for non-lyric items with `has_lyrics: false`, title set to `"Cuộc sống chill [timestamp]"`, and display a `🔇 Không có lyrics` status badge.
- **FR-007**: System MUST preserve all standard visual rendering rules (9:16 aspect ratio, 1080x1920 resolution, background brightness reduction, logo watermark, slideshow transitions if multi-image) regardless of whether lyrics are present.

### Key Entities

- **VideoQueueItem**: Represents a video in the processing queue. Contains metadata (`video_path`, `duration_s`, `has_lyrics`, `title`, `lyric_source`).
- **RenderOutput**: Represents the exported MP4 file. Contains file path, folder location (`outputs` vs `outputs-no-lyrics`), filename (`Cuộc sống chill [timestamp].mp4`), and media specs.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of videos identified as having no lyrics are rendered with zero lyric text overlay superimposed on the video canvas.
- **SC-002**: 100% of exported videos without lyrics are named with prefix `"Cuộc sống chill "` and a valid timestamp.
- **SC-003**: Rendering time for non-lyric videos decreases by at least 15% due to bypassing lyric image composition and text font rendering.
- **SC-004**: Zero rendering crashes or file collision overwrites occur when batch processing non-lyric videos.

---

## Assumptions

- Source video audio is always preserved as the audio track of the rendered output, even when lyrics overlay is skipped.
- Logo watermark (`logo-text.png`) remains placed on the upper right corner of non-lyric videos according to Constitution Principle II.
- Both single-image and multi-image slideshow modes support rendering without lyrics overlay.

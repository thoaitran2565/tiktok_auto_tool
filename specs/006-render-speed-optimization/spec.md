# Feature Specification: Fast Video Render Pipeline & Performance Optimization

**Feature Branch**: `006-render-speed-optimization`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "hiện tại thời gian để hoàn thành render ra 1 video mất khá lâu thời gian hãy tìm ra các giải pháp tốt nhất để tối ưu thời gian render này"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accelerated Video Encoding Engine (Priority: P1)

As a content creator producing batches of short-form videos, I want the media encoding stage (Stage 5) to finish in seconds rather than minutes, so that I can rapidly export finished videos without waiting 2 to 3 minutes for every 30-second clip.

**Why this priority**: Telemetry data reveals Stage 5 (Media Encoding) currently consumes 65% to 75% of total render time (~120s–140s per 35s video). Accelerating media encoding provides the largest immediate speedup across the entire system.

**Independent Test**: Render any video item in the queue. Measure the duration of Stage 5 (`media_encoding`). Verify that it completes in under 15–20 seconds (a 5x–10x reduction from ~130s), while maintaining 1080x1920 vertical resolution, audio sync, and sharp visual overlays.

**Acceptance Scenarios**:

1. **Given** a video ready for encoding, **When** the system renders the final video, **Then** it encodes the vertical 1080x1920 MP4 video using [NEEDS CLARIFICATION: encoding engine and hardware acceleration policy] with encoding time completing within 20% of video duration.
2. **Given** a video using a static background image, **When** media encoding runs, **Then** the engine avoids redundant per-frame Python image compositing, streaming the static canvas directly into the encoder.
3. **Given** a video using a multi-image slideshow, **When** media encoding runs, **Then** transitions composite at maximum encoder throughput without frame drops or memory leaks.

---

### User Story 2 - In-Memory Model Caching & Fast Transcription (Priority: P1)

As a creator rendering multiple videos in a session, I want speech recognition (Whisper) to execute swiftly without repeatedly reloading neural network weights from disk for every video, so that audio transcription completes in under 5–8 seconds instead of 20–40 seconds.

**Why this priority**: Whisper currently cold-loads model weights from disk on every single video execution (`whisper.load_model("small")`), adding 10–20 seconds of unnecessary disk I/O and initialization overhead per item.

**Independent Test**: Load multiple videos into the queue and execute rendering. Verify that the speech recognition model is initialized once in memory, reducing Stage 2 (`speech_transcription`) time from ~25s down to under 8s on subsequent items.

**Acceptance Scenarios**:

1. **Given** the application starts or renders its first video, **When** Stage 2 initiates, **Then** the speech recognition model is loaded into an in-memory cache and retained for subsequent queue items.
2. **Given** subsequent videos in the render queue, **When** Stage 2 runs, **Then** transcription begins immediately from the warmed in-memory model without re-reading model weights from disk.
3. **Given** user preference for maximum speed vs high transcription accuracy, **When** configuring the speech recognition engine, **Then** the system uses [NEEDS CLARIFICATION: Whisper model selection and execution engine].

---

### User Story 3 - Pipelined Background Processing for Batch Renders (Priority: P2)

As a creator processing a queue of 10+ videos, I want the system to pipeline non-competing stages (e.g., preparing audio and lyrics for the next video while the current video is encoding), so that total batch render time drops significantly through overlapped execution.

**Why this priority**: Currently, all 6 stages run in strict sequence per video, leaving the CPU idle during cloud API calls and network idle during media encoding. Overlapping independent stages eliminates downtime between queue items.

**Independent Test**: Queue 3 videos and click "Render Tất Cả". Monitor stage timelines to verify that while Video #1 is encoding in Stage 5, Video #2 concurrently executes Stage 1–3 (audio extraction and lyrics analysis), reducing aggregate queue completion time by at least 30%.

**Acceptance Scenarios**:

1. **Given** a queue with multiple items scheduled for rendering, **When** batch rendering executes, **Then** the pipeline operates according to [NEEDS CLARIFICATION: concurrency and stage pipelining architecture].
2. **Given** real-time progress indicators on the frontend, **When** pipelined stages run concurrently on adjacent items, **Then** the UI clearly reflects active states for each item without race conditions or telemetry data corruption.

---

### Edge Cases

- **Missing or incompatible GPU drivers**: If hardware acceleration (NVENC/QSV/AMF) is requested but unavailable on the host system, the encoder MUST seamlessly fall back to optimized software encoding without crashing or stopping the queue.
- **Low-memory systems during model caching**: If system RAM is constrained, the cached Whisper model MUST gracefully unload or release memory when idle.
- **Cloud API timeout or lag in Lyric Refinement**: If Gemini API latency exceeds 15 seconds, the system MUST apply an aggressive timeout and fall back to clean raw Whisper lyrics rather than stalling the pipeline for hundreds of seconds.
- **Audio and visual length mismatch**: When fast encoding is applied, output video duration MUST exactly match source audio duration down to the millisecond without audio cutoffs or lingering black frames.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The media encoding engine MUST reduce Stage 5 render duration by at least 70% compared to baseline (~130s baseline down to $\le 30$s for a 35s video).
- **FR-002**: The video pipeline MUST support direct stream muxing and optimized encoder presets (`ultrafast` / `superfast` or hardware encoder) while maintaining standard 1080x1920 vertical format.
- **FR-003**: The speech transcription module MUST cache the speech recognition model in memory as a singleton across all queue operations rather than re-loading from disk per video.
- **FR-004**: The AI lyric refinement module MUST enforce a strict timeout (max 15 seconds per model request) with graceful fallback to prevent cloud API delays from blocking video completion.
- **FR-005**: The render pipeline MUST clean up all temporary intermediate buffers and memory allocations immediately after each stage completes.
- **FR-006**: The queue system MUST maintain telemetry accuracy and stage status fidelity during accelerated and pipelined execution.
- **FR-007**: Rendered videos MUST maintain 100% compliance with Constitution Principle II: strict 1080x1920 vertical aspect ratio, 20% background dimming, upper-corner logo placement, and legible text contrast.
- **FR-008**: System MUST support configurable performance profiles (e.g. "Cân bằng / Tốc độ tối đa") accessible in settings or configuration.

### Key Entities

- **Performance Profile**:
  - `encoder_mode`: Encoder backend (`hardware_auto`, `nvenc`, `qsv`, `software_fast`).
  - `encoder_preset`: Encoding speed preset (`ultrafast`, `veryfast`).
  - `whisper_model`: Selected transcription model (`small`, `base`, `turbo`).
  - `model_cache_status`: State of the in-memory speech model (`unloaded`, `warm`, `ready`).
- **Stage Metrics**:
  - `stage_durations`: Detailed timings recorded per stage (audio, transcription, refinement, visual, encoding, finalization).
  - `speedup_factor`: Comparative acceleration factor relative to baseline telemetry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Single-video total render time for a standard 30–35s video is reduced from ~180–240 seconds down to under 45–60 seconds (overall speedup $> 3\times$).
- **SC-002**: Media encoding stage (Stage 5) duration is reduced from ~130s down to under 15–20s on systems with hardware acceleration, and under 30s on software fallback.
- **SC-003**: Speech transcription stage (Stage 2) duration on warmed queue items is reduced from ~25s down to under 8s.
- **SC-004**: 100% of generated videos retain full 1080x1920 vertical resolution, proper audio synchronization, and visual overlay readability.
- **SC-005**: Batch queue throughput (videos rendered per hour) increases by at least 250%.

## Assumptions

- Target host runs on modern Windows 10/11 environment with multi-core CPU and optional dedicated/integrated GPU (NVIDIA NVENC, Intel QuickSync, or AMD AMF).
- FFmpeg is available on the host system or bundled within the environment.
- Cloud Gemini API response times may vary due to network conditions, making local stage acceleration and strict network timeouts critical.


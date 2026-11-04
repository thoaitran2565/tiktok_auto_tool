# Feature Specification: Granular Render Progress Tracking and Predictive Estimation

**Feature Branch**: `001-render-progress-prediction`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Thêm tính năng hiển thị tiến độ render video trên giao diện, ví dụ đang trích xuất lời bài hát, đang làm sạch lời bài hát,... mỗi bước tiến độ đang đến đâu. thu thập thông tin trong mỗi lần render video để đưa ra dự đoán cho những lần render sau tùy vào độ dài video, dung lượng, tốc độ mạng, vv"

## Clarifications

### Session 2026-11-04
- Q: How should the granular render stages and progress be visually presented for each video item in the queue? → A: Option A — Compact inline status badge showing the active stage and animated indicator, expandable on click to reveal the detailed multi-step timeline and individual stage timings.
- Q: How should network performance and external API latency be incorporated into the render time prediction? → A: Option A — Track a rolling average of recent API request latencies and apply it specifically to the remote lyric refinement stage estimate.
- Q: How should historical render telemetry records be retained and managed in local storage? → A: Option A — Retain a rolling window of the last 100 completed renders, automatically pruning the oldest entries.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Granular Stage Progress Visibility (Priority: P1)

As a content creator generating batch short videos, I want to see exactly which stage of the rendering pipeline my video is currently in (e.g., extracting audio, transcribing speech, cleaning lyrics, composing visuals, final video encoding) along with an active progress indicator, so that I understand current processing status and know the system is actively working rather than frozen.

**Why this priority**: Users currently have minimal visibility into what happens during long render cycles. Breaking the render process down into discrete, transparent stages immediately improves usability, reduces user anxiety during processing pauses, and prevents premature cancellations.

**Independent Test**: Can be tested by queueing a single video for processing and observing that the user interface visibly transitions sequentially through each distinct pipeline stage with real-time visual status updates from start to completion.

**Acceptance Scenarios**:

1. **Given** a queued video starting processing, **When** the rendering pipeline begins, **Then** the interface displays an active step indicator naming the current phase (e.g., "Extracting audio") and marks previous phases as completed.
2. **Given** a video undergoing AI lyric processing, **When** speech recognition completes and text refinement begins, **Then** the progress interface updates immediately from "Transcribing speech" to "Refining lyrics" with a live elapsed time indicator.
3. **Given** an active rendering task, **When** any stage encounters an issue or error, **Then** the interface highlights the exact failing stage with a human-readable failure reason and ceases further progression for that item without disrupting the overall interface.
4. **Given** a video item with an active or completed render, **When** the user clicks the compact status badge or table row, **Then** the item expands inline to reveal the full sequential stage breakdown with individual stage durations and timestamps.

---

### User Story 2 - Render Telemetry & Performance Data Collection (Priority: P2)

As a system user, I want the system to automatically record key performance metrics for each completed video render (including input video duration, input file size, stage durations, and network round-trip latency for remote services), so that the application builds a performance history capable of informing future duration predictions.

**Why this priority**: Gathering empirical run metrics is an essential prerequisite for making accurate, personalized predictions on future render workloads without relying solely on arbitrary static estimates.

**Independent Test**: Can be tested by running multiple video renders with varying lengths and verifying that a persistent telemetry log records the input media characteristics, individual step elapsed times, and total duration for each run.

**Acceptance Scenarios**:

1. **Given** a video completes processing successfully, **When** the output file is verified, **Then** the system records an execution record capturing input duration, file size, timestamp, each stage's elapsed time, and total render duration.
2. **Given** external service calls occur during lyric processing, **When** the remote call completes, **Then** the system logs the round-trip response duration and marks whether the call succeeded or fell back to local processing.
3. **Given** multiple renders have occurred, **When** checking historical telemetry data, **Then** the records persist across application restarts.

---

### User Story 3 - Predictive Render Time Estimation (Priority: P3)

As a content creator managing a batch queue of videos, I want to see an estimated completion time and remaining countdown for active renders as well as expected processing times for items waiting in the queue based on historical performance, so that I can manage my time and anticipate when outputs will be ready.

**Why this priority**: Predictive estimations turn raw progress bars into actionable scheduling insight, allowing creators to plan other tasks while videos render.

**Independent Test**: Can be tested by queuing several videos of known duration and file size, verifying that each item displays an estimated processing duration, and that the active item updates its remaining time in real-time as stages complete.

**Acceptance Scenarios**:

1. **Given** videos in the processing queue, **When** the queue is loaded or updated, **Then** each item displays an estimated total render duration calculated from historical averages adjusted for its input length and file size.
2. **Given** an active video render in progress, **When** stages complete, **Then** the remaining time dynamically recalculates based on remaining stages and recent historical processing rates.
3. **Given** a fresh system with zero historical renders, **When** a video is queued, **Then** the system provides a provisional baseline estimate accompanied by a notice that predictions will improve as more videos are processed.

---

### Edge Cases

- **Cold Start (No Historical Telemetry)**: When no previous render telemetry is available, the system must utilize a baseline heuristic estimate (proportional to source video duration) rather than displaying blank or zero times.
- **Extreme Media Variations**: For unusually small (<5 seconds) or large (>15 minutes) input media, predictive models must clamp outlier ratios so estimates do not become wildly inaccurate.
- **External Service Outage / Degradation**: If remote services become unresponsive or slow, the active stage timer must reflect continued waiting without stalling the UI, and if a fallback occurs, the stage indicator must update to indicate fallback status.
- **Page Reload or Disconnect**: If the user reloads the browser tab while a render is actively running in the background, the UI must re-sync to the current stage, elapsed time, and remaining estimate upon reconnection.
- **Cancelled or Aborted Renders**: If an item is canceled midway, metrics up to the point of cancellation must be logged as aborted or omitted from prediction baselines to avoid corrupting predictive averages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST partition the video creation lifecycle into distinct, sequential observable stages: Audio Extraction, Speech Transcription, Lyric Refinement, Visual Generation, Media Encoding, and Finalization.
- **FR-002**: The user interface MUST display a compact inline status badge showing the current active stage name and status (Pending, In Progress, Completed, Failed) with an animated activity indicator for each item in the render queue, expandable on click to reveal full step breakdown and stage timings.
- **FR-003**: The system MUST provide real-time updates of the active stage and overall percentage completion to the user interface without requiring full page refreshes.
- **FR-004**: The system MUST track and display elapsed time for the currently processing video item.
- **FR-005**: The system MUST record a performance telemetry entry for every completed render, containing: unique item identifier, video duration (seconds), file size (megabytes), individual stage execution times (seconds), external service response latency, and total elapsed duration.
- **FR-006**: The telemetry records MUST be persisted in local storage so that performance data survives application restarts, maintaining a rolling window capped at the 100 most recent completed renders with automatic pruning of older records.
- **FR-007**: The system MUST calculate estimated stage and total render times for each queued video using a hybrid model: local stages (audio extraction, speech transcription, visual generation, video encoding) scaled by input video duration and file size, and the remote lyric refinement stage scaled by a rolling average of recent external API response latencies.
- **FR-008**: The system MUST dynamically compute and display the estimated remaining time (countdown) for the active render, adjusting as each stage concludes.
- **FR-009**: The prediction engine MUST implement a default fallback baseline for new installations with fewer than three completed historical renders.
- **FR-010**: The user interface MUST display overall queue completion estimates (total estimated time for all pending items in batch).
- **FR-011**: Telemetry collection MUST occur unobtrusively in the background without introducing noticeable latency to the video rendering pipeline.

### Key Entities

- **Render Stage**: Represents a single atomic phase within the video creation pipeline. Attributes include stage identifier, human-readable display label, stage order, status state (Pending, Active, Completed, Failed), started timestamp, and finished timestamp.
- **Item Progress State**: Represents the live processing status of a single video. Attributes include video identifier, current active stage, completed stages count, elapsed duration, estimated total duration, and estimated remaining duration.
- **Render Telemetry Record**: Represents an immutable log of a completed rendering task (retained up to a rolling window of 100 entries). Attributes include record timestamp, source video duration, source video file size, audio duration, duration per stage, network/remote service latency, total render duration, and completion status.
- **Prediction Model Profile**: Represents the aggregated statistical coefficients (average seconds per video minute, average seconds per megabyte, per-stage weight ratios, rolling API latency) derived from historical telemetry records to compute future estimates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view the exact operational stage and elapsed time of an ongoing render within 1 second of entering or refreshing the page.
- **SC-002**: Stage transition indicators in the UI update within 500 milliseconds of backend stage changes.
- **SC-003**: After 5 baseline renders on a given device, predicted completion times for subsequent renders match actual completion times within a ±25% margin of error under normal system conditions.
- **SC-004**: Telemetry recording operations complete with negligible overhead (less than 50 milliseconds of additional execution time per render run).
- **SC-005**: 100% of failed renders visibly pinpoint the specific stage that caused the failure, eliminating ambiguous generic error states.

## Assumptions

- **Local Execution**: The application runs in a local environment where local disk I/O and CPU availability are the primary determinants of video encoding speed.
- **Historical Data Privacy**: All telemetry is stored locally within the application data directory and is never transmitted to external third parties.
- **Baseline Default**: In the absence of historical telemetry (<3 runs), the initial duration estimate defaults to a 1.5x multiplier of the source video duration for standard quality renders.
- **Stage Granularity**: The 6 designated stages sufficiently capture all core user-facing operations without overwhelming the user with micro-step notifications.
- **Non-Blocking UI**: Progress information is communicated asynchronously so that the user interface remains interactive and responsive throughout multi-minute batch renders.
- **Network Latency Isolation**: Network latency affects solely the remote AI lyric refinement stage estimate and does not alter the coefficients calculated for local CPU/GPU media encoding stages.

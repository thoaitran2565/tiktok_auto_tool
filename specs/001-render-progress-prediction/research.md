# Research & Architecture Decisions: Granular Render Progress & Prediction

**Feature**: Granular Render Progress Tracking and Predictive Estimation  
**Branch**: `001-render-progress-prediction`  
**Date**: 2026-11-04  

---

## 1. Real-Time Progress Communication Architecture

### Decision
Use a lightweight REST polling endpoint (`GET /api/render-progress`) queried at 500ms intervals by the frontend client while a render is active, backed by an in-memory thread-safe progress store on the Flask backend.

### Rationale
- **Simplicity & Zero Extra Dependencies**: The application is a local web tool built on standard Flask and Python. Polling avoids the need for WebSocket servers, event loop changes, or ASGI frameworks like Quart/FastAPI.
- **Resilience to Reconnection & Tab Refresh**: REST polling is stateless over HTTP; if the user refreshes their browser tab, the next poll immediately re-syncs current progress, elapsed times, and estimated remaining duration without dropped connection errors.
- **Low Overhead**: A single local client polling at 500ms generates negligible CPU or memory impact (<0.1% CPU).

### Alternatives Considered
- **Server-Sent Events (SSE)**: Provides streaming updates over a persistent connection, but requires careful handling of thread workers, buffering in some reverse proxies or browsers, and can complicate reconnects after page reload.
- **WebSockets**: Overkill for a local single-user video rendering utility, requiring additional Python packages (`flask-socketio`, `gevent`/`eventlet`) that add dependency friction.

---

## 2. Pipeline Decoupling & Stage Reporting

### Decision
Extract the monolithic video rendering sequence in `app.py` into a modular `RenderPipeline` class located in `services/render_pipeline.py`. The pipeline receives a progress callback `on_stage_update(stage_id, status, details)` to report stage transitions without coupling media processing logic to HTTP request handling.

### Stages Identified:
1. `audio_extraction`: Truncating/extracting audio track from video source to temporary MP3.
2. `speech_transcription`: Running local Whisper model to extract raw transcript.
3. `lyric_refinement`: Calling Gemini API (with fallback models) to filter noise and retrieve verified lyrics.
4. `visual_generation`: Preprocessing background image (aspect ratio preservation, 20% brightness dampening) and rendering transparent subtitle overlay via Pillow.
5. `media_encoding`: Compositing video layers (background, image, logo, lyrics) and encoding with MoviePy/FFmpeg (H.264/AAC).
6. `finalization`: Validating output file integrity, saving entry to video database, cleaning temporary audio clips, and safely deleting original source video.

### Rationale
- Aligns directly with **Constitution Principle I (Pipeline Modularity & Decoupled Core)** and **Principle V (Observability)**.
- Each stage can measure its own start time, finish time, and duration independently.
- Decouples processing from the web layer, allowing future CLI execution or unit testing without Flask.

---

## 3. Telemetry Persistence & Storage Model

### Decision
Persist telemetry records in a dedicated local JSON file at `data/render_telemetry.json` (or `outputs/render_telemetry.json` if data directory is omitted). Telemetry management will be handled by a dedicated `TelemetryManager` class capped at a rolling window of the **100 most recent completed renders**.

### Telemetry Record Structure:
- `id`: Unique render ID (e.g., `vid_1699999999`)
- `timestamp`: ISO-8601 string
- `video_name`: Name of source video
- `input_duration_s`: Source audio/video length in seconds
- `input_size_mb`: File size in MB
- `stage_durations`: Mapping of stage ID to elapsed seconds (`audio_extraction`, `speech_transcription`, `lyric_refinement`, `visual_generation`, `media_encoding`, `finalization`)
- `api_latency_ms`: Round-trip latency of the Gemini API call in milliseconds
- `total_duration_s`: End-to-end processing time in seconds
- `status`: `"completed"` or `"failed"`

### Rationale
- 100 entries provide sufficient statistical sample size across diverse video lengths and file sizes while keeping file size under 50 KB.
- Local JSON requires no external database drivers and matches existing project persistence (`config.json`, `videos_db.json`).

---

## 4. Predictive Estimation Algorithm

### Decision
Implement a hybrid prediction formula combining local empirical ratios and rolling remote API latency:

$$\text{Estimated Total} = \left(\text{Input Duration} \times R_{\text{duration}}\right) + \left(\text{Input Size (MB)} \times R_{\text{size}}\right) + L_{\text{api}}$$

Where:
- $R_{\text{duration}}$: Empirical coefficient (mean of $\frac{\text{Local Duration}}{\text{Input Duration}}$ across last $N$ successful renders).
- $R_{\text{size}}$: Fine-tuning coefficient for file read/decode overhead.
- $L_{\text{api}}$: Exponential moving average (EMA) of recent Gemini API call latencies (defaults to 3.0s if no history).
- **Cold-Start Fallback**: If fewer than 3 historical records exist, default to:
  $$\text{Estimated Total} = 1.5 \times \text{Input Duration} + 4.0\text{s}$$
- **Clamping**: Bounded between minimum 5 seconds and maximum $3.5 \times \text{Input Duration}$.
- **Active Countdown**:
  $$\text{Remaining Time} = \max\left(1, \text{Estimated Total} - \text{Elapsed Time}\right)$$
  When a stage completes, the remaining time is refined by summing the expected historical durations of remaining stages.

### Alternatives Considered
- **Machine Learning (Scikit-Learn/Regression)**: Unnecessary computational overhead and heavy external dependencies for a lightweight local utility.
- **Static Multiplier**: Too rigid; fails to account for device differences (CPU speed vs GPU acceleration) or fluctuating Gemini API latency.


# Research: Lyrics Testing Page (/test)

**Feature**: `007-lyrics-test-page`  
**Date**: 2026-11-21  

---

## 1. Technical Decisions & Architectural Analysis

### Decision 1: Dedicated Route & Template (`/test` and `templates/test.html`)
- **Decision**: Create a dedicated Flask route `@app.route('/test')` serving `templates/test.html` rather than overloading `index.html` with query parameters (e.g. `/?mode=test`).
- **Rationale**: 
  - Clear separation of concerns between media production (heavy video generation) and audio/lyrics quality validation.
  - Allows `test.html` to have a streamlined setup bar (omitting image folder inputs) and a tailored table structure optimized for text inspection rather than video thumbnails and slideshow controls.
  - Reuses the shared CSS styling, colors, and font-awesome icon tokens for 100% visual consistency.
- **Alternatives Considered**:
  - *Adding a "Test Mode" toggle switch to `index.html`*: Discarded because `index.html` already contains complex multi-image slideshow pickers, video preview modals, and 6-stage render accordions. Toggling modes would add clutter and risk breaking render workflows.

---

### Decision 2: Isolated Backend Test Controller & Endpoints
- **Decision**: Introduce dedicated test API endpoints in `app.py`:
  - `POST /api/test-scan-videos`: Scans video files from a target directory using `ScannerService.scan_videos()` without requiring image files.
  - `POST /api/test-lyrics`: Accepts video path/ID, executes Stages 1–3 only (`extract_raw_lyrics` + `clean_lyrics_with_ai`), purges scratch audio, and returns text results immediately.
- **Rationale**:
  - Prevents test runs from polluting `videos_db.json` or `data/render_telemetry.json` with incomplete renders.
  - Guarantees 0 MB of video encoding outputs.
  - Enforces Principle III (Fail-safe resource management): temporary scratch audio file `outputs/temp_test_audio_<id>.mp3` is deleted in a `finally` block.
- **Alternatives Considered**:
  - *Running `render_pipeline.render()` and aborting at Stage 4*: Inefficient, as it involves progress manager state transitions, output folder resolution, and canvas composition logic that is irrelevant to lyrics testing.

---

### Decision 3: Reusing Warm `TranscriptionService` Singleton
- **Decision**: Directly invoke `TranscriptionService.transcribe(video_path)` from `extract_lyrics.py`.
- **Rationale**:
  - Feature 006 established `TranscriptionService` in-memory singleton. By reusing this warm model in memory, speech recognition on `/test` completes in 3–8 seconds per video without disk reload penalties.
  - Keeps RAM usage low since both `/` and `/test` share the same resident model instance.

---

### Decision 4: Interactive Side-by-Side Modal & Real-time Batch Controller
- **Decision**:
  - Implement a dedicated lyrics comparison modal in `test.html` with two side-by-side columns:
    - **Cột 1**: Lời thô nhận diện (Raw Whisper Transcript) with word count badge.
    - **Cột 2**: Lời AI hoàn chỉnh (Gemini Cleaned Lyrics) with song title header and source badge (`AI` vs `Original`).
    - One-click copy buttons for both columns.
  - Implement a client-side sequential batch testing loop with "Bắt Đầu Test Tất Cả" and "Dừng Lại" controls, showing real-time spinners and status updates per row.
- **Rationale**:
  - Meets all acceptance criteria specified by the user in Clarifications (Q1: Option A, Q2: Option A, Q3: Option A).

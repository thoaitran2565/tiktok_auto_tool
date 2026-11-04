# Implementation Plan: Granular Render Progress Tracking and Predictive Estimation

**Branch**: `001-render-progress-prediction` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-render-progress-prediction/spec.md`

## Summary

This feature replaces simulated, static progress bars with real-time, stage-by-stage rendering progress tracking across 6 distinct pipeline phases (Audio Extraction, Speech Transcription, Lyric Refinement, Visual Generation, Media Encoding, Finalization). It decouples the video rendering logic into a modular pipeline service, captures per-run empirical performance telemetry stored in a local rolling JSON log (capped at 100 records), and implements a hybrid prediction algorithm combining empirical device rendering rates with rolling remote API latency to predict accurate remaining and total durations for batch queues.

## Technical Context

**Language/Version**: Python 3.8+ (Windows execution environment)  
**Primary Dependencies**: Flask, MoviePy, Pillow (PIL), NumPy, OpenAI Whisper, Google GenAI SDK (`google.genai`), python-dotenv  
**Storage**: Local file system & JSON files (`config.json`, `videos_db.json`, and `data/render_telemetry.json`)  
**Testing**: Runnable verification scenarios detailed in `quickstart.md` and automated stage contract tests  
**Target Platform**: Local desktop web application (Windows 10/11 primary, cross-platform capable)  
**Project Type**: Local Web Application (Flask REST backend + Vanilla Dark Mode HTML/CSS/JS frontend)  
**Performance Goals**:
- UI stage transition updates delivered within 500ms of backend transition
- Telemetry recording overhead under 50ms per completed render
- Predictive estimation accuracy within ±25% of actual render time after 5 baseline runs  
**Constraints**:
- Strict offline/local execution for telemetry (no remote metric leaks)
- Bounded 100-item rolling telemetry retention (<100 KB disk footprint)
- Non-blocking asynchronous updates without freezing the browser UI  
**Scale/Scope**: Single-user local batches (typically 5 to 50 videos per session, source clips from 15s to 5m)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Compliance Analysis | Status |
|-----------|-------------|---------------------|--------|
| **I. Pipeline Modularity** | Core media processing decoupled from web request lifecycle; callable standalone | Rendering logic extracted from monolithic `app.py` into `services/render_pipeline.py` using observer/callback hooks. | **PASS** |
| **II. 9:16 Visual Standards** | 1080x1920 layout, distortion-free scaling, bounded lyrics | Preserves existing 1080x1920 canvas, aspect ratio letterboxing, 20% background dampening, and safe-height lyric overlay. | **PASS** |
| **III. Fail-Safe Media** | Intermediate cleanup & verified output before source removal | Dedicated `finalization` stage cleans intermediate temp audio and validates output MP4 presence before deleting input video. | **PASS** |
| **IV. Resilient AI** | Gemini fallback cascades & graceful fallback to raw text | Existing Whisper + Gemini cascade preserved; rolling API latency isolated to prevent network jitter from skewing local media encoding multipliers. | **PASS** |
| **V. Observability & Async** | Granular progress, structured logging, non-blocking execution | Directly addresses Principle V: provides 6 observable stages, elapsed time tracking, telemetry metrics, and predictive ETAs. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/001-render-progress-prediction/
├── spec.md              # Feature requirements and acceptance scenarios
├── plan.md              # This implementation plan
├── research.md          # Architecture decisions (polling vs SSE, hybrid prediction)
├── data-model.md        # Entities: RenderStage, ItemProgressState, RenderTelemetryRecord, PredictionModelProfile
├── quickstart.md        # Step-by-step verification and run scenarios
├── contracts/
│   └── render-progress-api.md # REST API contracts for progress, predictions, telemetry
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
tiktok_auto_render_tool/
├── app.py                          # Flask routes (serves endpoints, delegates to services)
├── config.json                     # Folder configuration
├── videos_db.json                  # Output videos catalog
├── extract_lyrics.py               # Whisper STT & Gemini API lyrics cleaning
├── services/
│   ├── __init__.py
│   ├── render_pipeline.py          # Modular 6-stage rendering engine with progress callbacks
│   ├── progress_manager.py         # Thread-safe in-memory state store for active items
│   └── telemetry_manager.py        # Persistent telemetry logger & duration prediction model
├── data/
│   └── render_telemetry.json       # Rolling 100-run performance history
├── templates/
│   ├── index.html                  # Queue dashboard with expandable stage stepper & ETAs
│   └── manage.html                 # Video library manager
└── outputs/                        # Output MP4 directory
```

**Structure Decision**:
Modular Service Layer: Rather than expanding `app.py` into a monolithic file, core logic is partitioned into `services/` (`render_pipeline.py`, `progress_manager.py`, `telemetry_manager.py`), keeping `app.py` clean as an orchestration and routing controller.

## Complexity Tracking

> *No Constitution violations detected. All gates pass cleanly.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | N/A | N/A |

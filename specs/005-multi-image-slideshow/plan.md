# Implementation Plan: Multi-Image Video Slideshow with Smooth Transitions

**Branch**: `005-multi-image-slideshow` | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-multi-image-slideshow/spec.md`

## Summary

This feature delivers end-to-end multi-image slideshow capability:
1. **Interactive Per-Video Configuration**: Adds a toggle switch to each queue row defaulting to 10 random images, with stepper buttons (`-`/`+`) to adjust count (2 to 50), and modal gallery curation allowing individual slot replacements or one-click batch re-rolls.
2. **Right-to-Left Slide Transition Compositor**: Builds a dedicated `services/slideshow_service.py` generating MoviePy video clips with smooth right-to-left horizontal slide transitions between sequential images, integrated into `services/render_pipeline.py` with standard 9:16 vertical formatting (`1080x1920`) and persistent lyrics/logo overlays per Constitution Principles I & II.

## Technical Context

**Language/Version**: Python 3.8+ (Server) / Vanilla ECMAScript 2022+ & CSS3 (Client)

**Primary Dependencies**: Flask, MoviePy 2.0+, Pillow (`PIL`), NumPy

**Storage**: Local in-memory session queue with JSON persistence (`videos_db.json`, `config.json`)

**Testing**: Python bytecode verification (`py_compile`), interactive browser validation per `quickstart.md`

**Target Platform**: Windows 10/11 Desktop Environment, Modern Desktop Browsers

**Project Type**: Local Web Automation Tool (Flask Controller + Domain Services + SPA Frontend)

**Performance Goals**: Slide transition rendering overhead < 15% compared to single image; 60 FPS client UI toggle & stepper updates; instant multi-image modal rendering

**Constraints**: Zero external frontend framework dependencies; strict 9:16 vertical resolution (`1080x1920`); clean clip closing to prevent memory leaks on Windows

**Scale/Scope**: Handles queues with hundreds of videos and image folders with 25,000+ files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Pipeline Modularity & Decoupled Core**: **PASS**. Slideshow generation is encapsulated in a dedicated standalone service (`services/slideshow_service.py`), testable independently without Flask.
- **Principle II: Standard 9:16 Media Formatting & Visual Integrity**: **PASS**. Every slide is pre-processed with Pillow to 1080x1920 without stretching, applying 20% background dimming for optimal text contrast.
- **Principle III: Fail-Safe Media & Resource Management**: **PASS**. Explicit clip cleanup (`clip.close()`) prevents resource exhaustion and Windows file locking.
- **Principle IV: Resilient AI & External Service Degradation**: **PASS**. Whisper transcription and Gemini NLP cascades remain uncoupled from background visual rendering.
- **Principle V: Observability & Asynchronous Processing**: **PASS**. Real-time progress updates and telemetry monitoring continue without disruption.

## Project Structure

### Documentation (this feature)

```text
specs/005-multi-image-slideshow/
├── spec.md              # Feature specification & clarifications
├── plan.md              # This implementation plan
├── research.md          # Technical decisions & MoviePy animation approach
├── data-model.md        # Extended QueueItem & Slideshow spec
├── quickstart.md        # Validation scenarios
├── contracts/
│   ├── multi-image-api-contract.md   # API & Service contracts
│   └── multi-image-ui-contract.md    # DOM & UI component contracts
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code Layout

```text
d:\Code\tools\tiktok_auto_render_tool/
├── app.py                      # Slim HTTP controller
├── services/
│   ├── config_service.py       # Configuration read/write
│   ├── scanner_service.py      # Non-blocking lazy media discovery
│   ├── queue_service.py        # In-memory queue state & multi-image persistence
│   ├── slideshow_service.py    # NEW: MoviePy right-to-left slide compositor
│   ├── render_pipeline.py      # Integrated 6-stage rendering pipeline
│   ├── progress_manager.py     # Live progress tracking
│   └── telemetry_manager.py    # Telemetry and prediction
└── templates/
    └── index.html              # Frontend UI with toggle switch, steppers & curation modal
```

**Structure Decision**: Monolithic domain service architecture. `app.py` exposes thin endpoints, `QueueService` stores multi-image metadata, `SlideshowService` generates the slide clips, and `render_pipeline.py` composites the final video.

## Complexity Tracking

*No violations identified. Fully compliant with Constitution principles.*

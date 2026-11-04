# Implementation Plan: Modal Image Wheel Zoom & Application Logic Decoupling

**Branch**: `004-modal-zoom-and-modularization` | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-modal-zoom-and-modularization/spec.md`

## Summary

This feature delivers two synchronized capabilities:
1. **Interactive Modal Image Wheel Zoom & Pan**: Equips modal preview stages with smooth GPU-accelerated wheel zooming (1.0x to 5.0x), drag panning, double-click reset, and zoom percentage badge feedback with zero page scroll leakage.
2. **Core Domain Services Decoupling**: Extracts folder scanning, queue management, duration estimation, and configuration I/O from `app.py` into dedicated modules (`services/config_service.py`, `services/scanner_service.py`, `services/queue_service.py`), reducing `app.py` to a clean controller layer (<280 lines) in strict accordance with Constitution Principle I.

## Technical Context

**Language/Version**: Python 3.8+ (Server) / Vanilla ECMAScript 2022+ & CSS3 (Client)

**Primary Dependencies**: Flask, Pillow, MoviePy (Server); HTML5 Canvas/CSS3 2D Transform (Client); FontAwesome 6 (Icons)

**Storage**: Local JSON files (`config.json`, `videos_db.json`, `data/telemetry.json`)

**Testing**: Pytest / Python py_compile syntax verification & manual interactive UI validation

**Target Platform**: Windows 10/11 Desktop Environment, Modern Desktop Browsers (Edge, Chrome, Firefox)

**Project Type**: Local Web Automation Application (Flask Backend + Vanilla HTML/CSS/JS Single-Page Frontend)

**Performance Goals**: 60 FPS transform rendering on client wheel/drag; <0.05s server folder scan & queue sync; <50ms zoom reset

**Constraints**: Zero external frontend NPM dependencies; strict non-blocking directory scanning (lazy iterator max 60 images); 100% backward compatibility for all API endpoints

**Scale/Scope**: Local workstation media processing; handles directories with 25,000+ images and hundreds of videos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Pipeline Modularity & Decoupled Core**: **PASS**. Directly advances this principle by extracting folder scanning, video queue mutation, duration estimation, and config management into standalone domain service modules outside the Flask request lifecycle.
- **Principle II: Standard 9:16 Media Formatting & Visual Integrity**: **PASS**. Preview zoom scales images uniformly with CSS transforms, preserving aspect ratios and 9:16 layout integrity.
- **Principle III: Fail-Safe Media & Resource Management**: **PASS**. Non-destructive operations; leaves source and target media pipelines completely intact with safe error guards.
- **Principle IV: Resilient AI & External Service Degradation**: **PASS**. No changes to AI cascades; keeps existing fallbacks untouched.
- **Principle V: Observability & Asynchronous Processing**: **PASS**. Maintains non-blocking async execution, progress polling, and telemetry managers without UI freezing.

## Project Structure

### Documentation (this feature)

```text
specs/004-modal-zoom-and-modularization/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Technical decisions & research
├── data-model.md        # Client and server data models
├── quickstart.md        # Verification and testing scenarios
├── contracts/
│   ├── modal-zoom-ui-contract.md   # Client DOM and event contracts
│   └── services-api-contract.md    # Service interfaces & controller mapping
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code Layout

```text
d:\Code\tools\tiktok_auto_render_tool/
├── app.py                      # Slim HTTP controller (<280 lines)
├── config.json                 # Directory configurations
├── services/
│   ├── __init__.py
│   ├── config_service.py       # Configuration read/write persistence
│   ├── scanner_service.py      # Non-blocking lazy media discovery
│   ├── queue_service.py        # In-memory queue state & sync
│   ├── progress_manager.py     # Live progress tracking
│   ├── telemetry_manager.py    # Render telemetry & estimation
│   └── render_pipeline.py      # Core decoupled render pipeline
└── templates/
    ├── index.html              # Frontend UI with wheel zoom controller
    └── manage.html             # Video library management UI
```

**Structure Decision**: Monolithic project organized by dedicated domain services under `services/`. `app.py` serves exclusively as the HTTP routing/controller layer. Frontend assets remain self-contained in standard Flask templates without build step requirements.

## Complexity Tracking

*No violations identified. Fully compliant with Constitution and architectural standards.*

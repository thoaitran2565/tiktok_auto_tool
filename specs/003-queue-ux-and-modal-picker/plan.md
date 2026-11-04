# Implementation Plan: Queue UX Refinements, Modal Image Picker, and Real-Duration Prediction

**Branch**: `003-queue-ux-and-modal-picker` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-queue-ux-and-modal-picker/spec.md`

## Summary

This feature resolves 8 critical UX friction points and algorithmic inaccuracies identified during production batch rendering:
1. Fixes active row auto-scroll calculation to account for the sticky table header offset.
2. Permanently locks source video preview and image modification controls on completed rows.
3. Automatically collapses the folder setup section into a 34px summary bar to maximize vertical table space.
4. Replaces the hardcoded 30-second duration constant with actual probed video durations and calibrated regression models.
5. Streamlines the first table column by omitting redundant filename text.
6. Replaces the legacy `<select>` dropdown with an interactive modal image picker featuring a horizontal carousel, random picker, and visual confirmation.
7. Ensures Step 6 (Finalization) reliably displays a completed checkmark upon video finish.
8. Upgrades the "Làm Mới" control into a non-destructive asynchronous data refresh that preserves active renders.

## Technical Context

**Language/Version**: Python 3.8+ (Windows execution environment)  
**Primary Dependencies**: Flask, MoviePy, Pillow, NumPy, OpenAI Whisper, Google GenAI SDK, python-dotenv  
**Storage**: Local files (`videos_db.json`, `data/render_telemetry.json`, `config.json`)  
**Testing**: Verification scenarios in `quickstart.md`  
**Target Platform**: Desktop Web Application (Windows 10/11 primary, cross-platform)  
**Project Type**: Local Web Application (Flask REST + Vanilla JS dark mode)  
**Performance Goals**:
- Active row auto-scroll positioned flush within 4px of sticky table header bottom with 0px overlap
- Screen real estate consumed by setup section decreased by >65% in collapsed state
- Estimation error on non-30s videos reduced by >50%
- Zero pipeline interruptions when clicking "Làm Mới" mid-render  
**Constraints**:
- Strict 9:16 formatting preserved
- Completed rows locked against accidental mutation
- Non-destructive queue refresh must append newly detected files seamlessly

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Compliance Analysis | Status |
|-----------|-------------|---------------------|--------|
| **I. Pipeline Modularity** | Core media processing decoupled from web request lifecycle | Real duration probing decoupled in utility/service layer; non-destructive refresh operates via dedicated REST endpoint. | **PASS** |
| **II. 9:16 Visual Standards** | 1080x1920 layout and visual consistency | Modal image picker and video viewers strictly preserve vertical 9:16 aspect ratio. | **PASS** |
| **III. Fail-Safe Media** | Intermediate cleanup & verified output before source removal | Completed rows locked against mutation prevents inconsistent media overwrites; probe failure safely defaults to baseline duration. | **PASS** |
| **IV. Resilient AI** | Fallback cascades & graceful degradation | Video duration probe failures gracefully fallback without failing folder scan or batch queue. | **PASS** |
| **V. Observability & Async** | Granular progress, structured logging, non-blocking execution | Real-duration predictive model dramatically improves ETA accuracy; non-destructive refresh and 6/6 step checkmarks guarantee full observability. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/003-queue-ux-and-modal-picker/
├── spec.md              # Feature requirements and acceptance scenarios
├── plan.md              # This implementation plan
├── research.md          # Architectural decisions (sticky offset, carousel picker, real-duration probe)
├── data-model.md        # Entities: QueueItemState, ImagePickerState, SetupSectionState, PredictiveModelParameters
├── quickstart.md        # 8 verification scenarios
├── contracts/
│   └── queue-api.md     # REST contracts for load-folders, refresh-queue, update-queue, predictions
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
tiktok_auto_render_tool/
├── app.py                      # Probed video duration in load-folders & predictions; added POST /api/refresh-queue
├── services/
│   ├── render_pipeline.py      # Core rendering pipeline
│   ├── progress_manager.py     # Guaranteed 6/6 step checkmarks
│   └── telemetry_manager.py    # Calibrated real-duration predictive estimation formula
└── templates/
    └── index.html              # Sticky header offset scroll, auto-compact setup bar, modal carousel picker, non-destructive refresh
```

## Complexity Tracking

> *No Constitution violations detected. All gates pass cleanly.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | N/A | N/A |

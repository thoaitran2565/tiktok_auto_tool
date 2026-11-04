# Implementation Plan: Render UX Optimizations, Adaptive Queue Learning, and Output Routing

**Branch**: `002-render-ux-and-output-routing` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-render-ux-and-output-routing/spec.md`

## Summary

This feature transforms the tool into a professional, desktop-like web application by anchoring the UI within the viewport height (`100vh`) with fixed sticky header controls, auto-scrolling and auto-expanding the active video during batch runs, formatting all timers strictly as integer seconds, implementing stage-boundary progress plateauing, dynamically re-calculating queue duration predictions as each video completes, routing non-lyric videos into a dedicated `outputs-no-lyrics/` directory with visual badges, adding a modal lightbox for media inspection, and streamlining terminal output into clean single-line logs.

## Technical Context

**Language/Version**: Python 3.8+ (Windows execution environment)  
**Primary Dependencies**: Flask, MoviePy, Pillow (PIL), NumPy, OpenAI Whisper, Google GenAI SDK, python-dotenv  
**Storage**: Local directories (`outputs/`, `outputs-no-lyrics/`, `data/render_telemetry.json`, `videos_db.json`)  
**Testing**: Verification scenarios in `quickstart.md`  
**Target Platform**: Local desktop web application (Windows 10/11 primary, cross-platform)  
**Project Type**: Local Web Application (Flask REST backend + Vanilla JS Dark Mode frontend)  
**Performance Goals**:
- Main viewport fits within 100vh with zero outer page scrollbars on screens >= 700px height
- Active row smooth auto-scroll and timeline auto-expansion within 200ms of starting
- 100% of timers formatted in integer seconds
- Terminal log volume reduced by >60% in line count  
**Constraints**:
- Strict 9:16 layout integrity maintained
- Output routing strictly separated between `outputs/` and `outputs-no-lyrics/`
- Modal viewer must dismiss on close button or backdrop click

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Compliance Analysis | Status |
|-----------|-------------|---------------------|--------|
| **I. Pipeline Modularity** | Core media processing decoupled from web request lifecycle | Output routing and logging cleanup implemented cleanly within `RenderPipeline` without coupling to Flask routing. | **PASS** |
| **II. 9:16 Visual Standards** | 1080x1920 layout and visual consistency | All videos whether lyric-enhanced or speechless retain identical 1080x1920 canvas and aspect ratios. | **PASS** |
| **III. Fail-Safe Media** | Intermediate cleanup & verified output before source removal | Both `outputs/` and `outputs-no-lyrics/` files verified for existence and non-zero size before deleting source files. | **PASS** |
| **IV. Resilient AI** | Fallback cascades & graceful degradation | When AI lyrics fail or are absent, video generation does not crash; it gracefully saves into `outputs-no-lyrics/`. | **PASS** |
| **V. Observability & Async** | Granular progress, structured logging, non-blocking execution | Terminal logging restructured to clean emoji single lines; UI progress enhanced with auto-scroll and integer timers. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/002-render-ux-and-output-routing/
├── spec.md              # Feature requirements and acceptance scenarios
├── plan.md              # This implementation plan
├── research.md          # Architecture decisions (100vh flex, plateauing, routing, modal)
├── data-model.md        # Entities: VideoRecord, QueueItemState, MediaModalState, StageBoundaryDefinition
├── quickstart.md        # Step-by-step verification guide
├── contracts/
│   └── output-routing-api.md # REST API contracts for outputs-no-lyrics and media preview
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
tiktok_auto_render_tool/
├── app.py                          # Added routes for outputs-no-lyrics and download handling
├── extract_lyrics.py               # Cleaned up console logs; suppressed verbose prompt dumps
├── services/
│   ├── render_pipeline.py          # Output folder routing logic (outputs vs outputs-no-lyrics) & concise logs
│   ├── progress_manager.py         # Integer second formatting helper & stage timing
│   └── telemetry_manager.py        # Adaptive duration prediction engine
├── outputs/                        # Standard output folder for videos with AI lyrics
├── outputs-no-lyrics/              # Dedicated output folder for videos without AI lyrics
├── templates/
│   ├── index.html                  # 100vh layout, sticky header, modal lightbox, auto-scroll, plateau progress
│   └── manage.html                 # Video manager page with has_lyrics badges
└── data/
    └── render_telemetry.json       # Historical performance records
```

## Complexity Tracking

> *No Constitution violations detected. All gates pass cleanly.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | N/A | N/A |

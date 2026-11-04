# Phase 0: Research & Technical Decisions

**Feature**: Modal Image Wheel Zoom & Application Logic Decoupling  
**Date**: 2026-11-04  
**Branch**: `004-modal-zoom-and-modularization`  

## 1. Modal Wheel Zoom & Pan Implementation

### Decision
Implement CSS 2D Transform (`transform: translate(x, y) scale(s)`) with GPU hardware acceleration on the modal preview image elements (`#modalCandidateImg` in curation modal and `.media-modal-body img` in lightbox modal). Manage zoom and pan state via a dedicated client-side controller object with normalized wheel delta throttling, event delegation, and boundary clamping.

### Rationale
- **60 FPS Performance**: Directly modifying image width/height triggers browser reflow and layout recalculation, which stutters on high-resolution images. CSS transforms run entirely on the GPU compositor thread with no reflow.
- **Scroll Isolation**: Binding `{ passive: false }` event listeners on the image container allows `e.preventDefault()`, completely preventing the host document or queue table from scrolling during zoom operations.
- **Smooth Cursor Origin**: Calculating zoom delta relative to pointer position or center keeps the image anchored intuitively during magnification.
- **Lifecycle Cleanliness**: Zoom transforms must be reset to 1.0x scale and 0 offsets whenever:
  1. A new thumbnail is clicked in the modal carousel.
  2. The "Chọn ngẫu nhiên" button is clicked.
  3. The modal is closed via close button, backdrop click, or Escape key.

### Alternatives Considered
- *Third-party libraries (e.g. panzoom, viewerjs, medium-zoom)*: Rejected to avoid external CDN dependencies, script bloat, and license overhead. Native vanilla JS with CSS transforms requires less than 70 lines of clean code and has zero external dependencies.
- *Native CSS `zoom` property*: Rejected because `zoom` is non-standard, behaves inconsistently across Firefox and WebKit, and does not support 2D smooth panning.

---

## 2. Decoupling Business & Media Services from `app.py`

### Decision
Decompose domain logic from `app.py` into three focused service modules under the `services/` namespace directory:
1. `services/config_service.py`: Encapsulates reading, validating, and persisting `config.json`.
2. `services/scanner_service.py`: Encapsulates non-blocking lazy folder scanning (`os.scandir` limited to 60 sample images), fast video file enumeration with instantaneous size-based duration heuristics, and whole-directory random image selection (`/api/random-image`).
3. `services/queue_service.py`: Encapsulates thread-safe in-memory session queue management, non-destructive queue synchronization (`refresh_queue`), item image reassignment, lock tracking, and telemetry prediction queries.

### Rationale
- **Constitution Principle I Alignment**: Principle I explicitly dictates: *"Media processing routines ... MUST operate as decoupled, standalone modules with strict input/output contracts. Core video processing logic MUST NOT be tightly bound to the Flask HTTP request cycle"*.
- **Maintainability & Readability**: Reduces `app.py` from over 600 lines down to under 250 lines of clean HTTP route definitions that delegate directly to service calls and return JSON responses.
- **Testability**: Service methods can be unit tested directly in scripts or test runners without mocking Flask application contexts, request headers, or HTTP client sessions.
- **Backwards Compatibility**: All API route paths, JSON payload schemas, and response keys remain 100% identical.

### Alternatives Considered
- *Flask Blueprints architecture*: Considered splitting into Blueprints (`queue_bp`, `media_bp`, `admin_bp`), but determined to be excessive ceremony for a single-developer desktop automation tool. Domain service modules provide better testability and cleaner separation without Flask routing overhead.
- *Leaving code in `app.py`*: Violates Principle I, causes cognitive overload, and increases bug regression risks when touching queue or scanning logic.

---

## 3. Zoom Clamping & Drag Boundaries

### Decision
- **Zoom range**: Clamp `scale` between `1.0` (fit-to-box) and `5.0` (maximum 500% magnification).
- **Zoom step**: Multiplier of `0.15` per wheel tick (`scale = scale * (1 - e.deltaY * 0.0015)`).
- **Drag activation**: Panning is only enabled when `scale > 1.05`. When `scale <= 1.0`, cursor remains default and drag events are ignored.
- **Visual Feedback**: Render an unobtrusive zoom pill badge (e.g. `150%`) positioned in the upper-right corner of the image stage whenever `scale > 1.0`, fading out when reset to 100%.

### Alternatives Considered
- *Uncapped zoom (e.g. up to 20x)*: Leads to visual pixel blur and easy user disorientation. 5.0x is optimal for inspecting 1080x1920 short-form video assets.


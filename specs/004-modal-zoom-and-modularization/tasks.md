# Tasks: Modal Image Wheel Zoom & Application Logic Decoupling

**Input**: Design documents from `/specs/004-modal-zoom-and-modularization/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Organization**: Tasks are grouped by foundational prerequisites and user stories to enable independent implementation and testing.

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Clear action and exact file path in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize service module structure

- [X] T001 Initialize package structure and verify `services/__init__.py` exists in `services/__init__.py`

---

## Phase 2: Foundational (Core Domain Services)

**Purpose**: Build standalone domain service modules that execute independently of Flask routing

- [X] T002 [P] Implement `ConfigService` in `services/config_service.py` for persistent configuration loading, validation, and saving per `contracts/services-api-contract.md`
- [X] T003 [P] Implement `ScannerService` in `services/scanner_service.py` for lazy image scanning (max 60 images via `os.scandir`), fast video enumeration, random image selection, and duration extraction per `contracts/services-api-contract.md`
- [X] T004 Implement `QueueService` in `services/queue_service.py` managing in-memory queue state, folder initialization, non-destructive synchronization, and item updates per `contracts/services-api-contract.md`

**Checkpoint**: Core domain services implemented and independently testable without Flask web server.

---

## Phase 3: User Story 2 - Decoupled Core Services & Routing Architecture (Priority: P1)

**Goal**: Refactor `app.py` into a thin HTTP controller layer delegating all business logic to services, achieving Constitution Principle I compliance.

**Independent Test**: Verify `app.py` line count is under 280 lines and all endpoints (`/api/load-folders`, `/api/refresh-queue`, `/api/update-queue`, `/api/random-image`, `/api/get-config`) respond with 100% functional parity and <0.05s latency.

### Implementation for User Story 2

- [X] T005 [US2] Refactor `app.py` to route all queue, folder, and configuration requests through `ConfigService`, `ScannerService`, and `QueueService` per `contracts/services-api-contract.md`
- [X] T006 [US2] Verify `app.py` code size reduction (<280 lines) and validate Python syntax via `python -m py_compile app.py services/config_service.py services/scanner_service.py services/queue_service.py`

**Checkpoint**: `app.py` is decoupled, fully modular, and all existing API contracts function identically.

---

## Phase 4: User Story 1 - Interactive Mouse Wheel Zoom & Pan in Image Modals (Priority: P1)

**Goal**: Enable smooth mouse wheel zoom (1.0x to 5.0x), pan dragging, and scroll isolation on modal image preview stages.

**Independent Test**: Open an image in the image swap modal, scroll mouse wheel to zoom in/out smoothly without scrolling the parent page, drag to pan when magnified, and double-click to reset view to 1.0x.

### Implementation for User Story 1

- [X] T007 [US1] Add CSS styles for `.modal-preview-stage`, GPU-accelerated 2D transforms, overflow containment, and grabbing cursors in `templates/index.html`
- [X] T008 [US1] Implement `ModalZoomController` with wheel event throttling, zoom clamping (1.0x to 5.0x), page scroll prevention (`e.preventDefault()`), and drag-to-pan tracking in `templates/index.html`
- [X] T009 [US1] Integrate zoom reset triggers into `openImagePickerModal`, `selectCandidateImage`, `pickRandomImage`, `closeMediaModal`, and double-click handler in `templates/index.html`

**Checkpoint**: User Story 1 fully functional and testable independently.

---

## Phase 5: User Story 3 - Visual Feedback and Zoom Controls in Modal Viewer (Priority: P2)

**Goal**: Display an unobtrusive zoom percentage pill badge and a quick reset button over the modal image preview stage.

**Independent Test**: Magnify an image past 100% and verify the zoom pill displays the current percentage (e.g. `160%`, `220%`), and clicking the reset icon button restores 100% fit.

### Implementation for User Story 3

- [X] T010 [US3] Add `#modalZoomBadge` and `#modalZoomResetBtn` elements into `.modal-preview-stage` in `templates/index.html`
- [X] T011 [US3] Bind zoom badge text updates and reset button click handler to `ModalZoomController.reset()` in `templates/index.html`

**Checkpoint**: User Story 3 operational with explicit visual status and click-to-reset accessibility.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end verification and quality checks

- [X] T012 [P] Verify clean importability and syntax across all `services/*.py` and `app.py` modules
- [X] T013 Execute full validation scenarios against `specs/004-modal-zoom-and-modularization/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1; blocks User Stories 1 and 2.
- **User Story 2 (Phase 3)**: Depends on Phase 2 services (`ConfigService`, `ScannerService`, `QueueService`).
- **User Story 1 (Phase 4)**: Can start after Phase 2; updates frontend `templates/index.html`.
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 4).
- **Polish (Phase 6)**: Runs after all user story phases complete.

### Parallel Opportunities

- `T002` (`config_service.py`) and `T003` (`scanner_service.py`) can run in parallel.
- `T005` (backend refactor) and `T007` (frontend CSS) can run in parallel once foundations are set.
- `T012` syntax check can run independently in parallel.

---

## Implementation Strategy

### MVP Scope (User Story 1 & User Story 2)
1. Complete Phase 1 & 2: Build `services/config_service.py`, `services/scanner_service.py`, `services/queue_service.py`.
2. Complete Phase 3: Slim down `app.py` and verify all endpoints pass.
3. Complete Phase 4: Implement wheel zoom and pan in `templates/index.html`.
4. Validate MVP: Test folder scan, queue load, and wheel zoom on images.
5. Complete Phase 5 & 6: Add zoom badge, quick reset button, and complete quickstart verification.

---

## Phase 7: Convergence

- [X] T014 Extract queue progress summary and prediction aggregation methods into `services/queue_service.py` to streamline `app.py` under 280 lines per SC-003, FR-010 (partial)


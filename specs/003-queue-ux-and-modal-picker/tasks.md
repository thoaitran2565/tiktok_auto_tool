---
description: "Task list for Queue UX Refinements, Modal Image Picker, and Real-Duration Prediction"
---

# Tasks: Queue UX Refinements, Modal Image Picker, and Real-Duration Prediction

**Input**: Design documents from `specs/003-queue-ux-and-modal-picker/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/queue-api.md`, `quickstart.md`, `checklists/full-scope.md`)  
**Prerequisites**: `plan.md`, `spec.md`, `constitution.md`  
**Organization**: Tasks are organized into 4 independent User Story phases (P1 through P4), flanked by Setup, Foundational, and Polish phases.

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no conflicting state dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify development baseline, file access, and module dependencies.

- [X] T001 Inspect current workspace and verify `videos_db.json`, `data/render_telemetry.json`, and route handlers in `app.py`
- [X] T002 [P] Verify MoviePy / FFmpeg media duration probing utility availability in Python runtime for `app.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and telemetry predictive parameters that block user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 [P] Update `QueueItemState` schema in `app.py` to support `duration_s: float` (probed actual duration in seconds, fallback default 30.0), `is_locked: bool` (default False, True when status === "Hoàn thành"), and status enum `"Chờ render" | "Đang render" | "Hoàn thành" | "Lỗi"`
- [X] T004 [P] Update `services/telemetry_manager.py` with `PredictiveModelParameters` defaults (`fixed_overhead_s: 8.0`, `avg_duration_ratio: 1.25`, `size_penalty_ratio: 0.02`) and update `predict_duration(duration_s, size_mb)` signature to accept media duration

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Seamless Queue Interaction & Viewport Optimization (Priority: P1) 🎯 MVP

**Goal**: Automatically collapse the folder setup section into a 34px summary bar, streamline Column 1 by removing verbose filename text, fix active row auto-scroll offset under the sticky table header (`scrollTop = row.offsetTop - 42`), and permanently lock preview/edit controls on completed rows.

**Independent Test**: Scan folders with 10+ videos. Verify the setup inputs collapse into a 34px bar (`📁 Ảnh: X tệp • 🎬 Video: Y tệp`) with a working "Đổi thư mục" button. Check that Column 1 displays only index `#`, ETA badge, and preview toggle without text filename. Start rendering and verify active row scrolls flush below sticky header `<th>` (within 4px clearance, 0px overlap). Verify finished video rows lock source preview and image editing controls.

### Implementation for User Story 1

- [X] T005 [P] [US1] Add CSS styles for collapsed setup summary bar (34px height), locked row controls (`pointer-events: none; opacity: 0.5`), and streamlined Column 1 in `templates/index.html`
- [X] T006 [US1] Implement `SetupSectionState` auto-collapse logic upon successful scan and "Đổi thư mục" re-expansion toggle in `templates/index.html`
- [X] T007 [P] [US1] Refactor queue table row template to streamline Column 1 ("Video Nguồn") displaying only index `#`, duration prediction badge, and preview toggle button (omitting verbose filename text) in `templates/index.html`
- [X] T008 [US1] Implement row-locking logic in `renderQueueTable()` to disable "Hiện video" button and image click modal trigger for items with `status === "Hoàn thành"` (`is_locked: true`) in `templates/index.html`
- [X] T009 [US1] Refactor `scrollToActiveRow()` to calculate `tableContainer.scrollTop = row.offsetTop - 42` ensuring active row aligns flush below sticky table header (`<th>`) without clipping in `templates/index.html`

**Checkpoint**: At this point, User Story 1 (MVP) is fully functional and testable independently.

---

## Phase 4: User Story 2 - Interactive Modal Image Picker with Preview Confirmation (Priority: P2)

**Goal**: Replace the legacy `<select>` dropdown in Column 2 with an interactive curation modal in `#mediaModal` featuring a horizontal thumbnail carousel, "Chọn ngẫu nhiên" (Random) button, and live stage preview before confirming changes.

**Independent Test**: Click an image thumbnail in Column 2 for an uncompleted item. Verify modal opens with high-resolution preview and bottom thumbnail carousel. Click another thumbnail or "Chọn ngẫu nhiên" to preview changes live. Click "Xác nhận đổi ảnh" and verify thumbnail updates in table and server persists selection via `POST /api/update-queue`.

### Implementation for User Story 2

- [X] T010 [P] [US2] Remove legacy `<select class="form-select">` dropdown from Column 2 ("Ảnh Ghép Mẫu") in `templates/index.html`, displaying only clickable thumbnail with cursor indicator for uncompleted items
- [X] T011 [P] [US2] Implement HTML markup and CSS styling for `#mediaModal` curation toolbar, candidate thumbnail carousel container, and "Xác nhận đổi ảnh" / "Hủy" buttons in `templates/index.html`
- [X] T012 [US2] Implement `ImagePickerState` management, carousel thumbnail population from `availableImages`, and stage selection preview in `templates/index.html`
- [X] T013 [US2] Implement "Chọn ngẫu nhiên" (Random) selection logic with single-image guard handling in `templates/index.html`
- [X] T014 [US2] Implement "Xác nhận đổi ảnh" handler dispatching `POST /api/update-queue` with `{ id, image_name }` and updating table thumbnail upon success in `templates/index.html`

**Checkpoint**: At this point, User Stories 1 AND 2 are both fully functional and testable independently.

---

## Phase 5: User Story 3 - Real-Duration Accurate Predictive Estimation (Priority: P3)

**Goal**: Probe actual media duration in seconds during folder scanning, pass real durations to telemetry model, and compute realistic render duration predictions scaling with media length.

**Independent Test**: Scan a folder with diverse video lengths (e.g. 10s clip vs 60s clip). Verify duration predictions scale proportionally with length (e.g. 10s -> ~18s-22s, 60s -> ~75s-90s) rather than defaulting blindly to a uniform ~45s estimate.

### Implementation for User Story 3

- [X] T015 [P] [US3] Implement fast video duration probe helper using `VideoFileClip` / FFmpeg with defensive try/except fallback (`default 30.0s`) in `app.py`
- [X] T016 [US3] Integrate video duration probing into `POST /api/load-folders` in `app.py` to populate `duration_s` for all scanned queue items
- [X] T017 [US3] Update `predict_duration` in `services/telemetry_manager.py` using calibrated formula `max(12, int(fixed_overhead_s + (duration_s * avg_duration_ratio) + (size_mb * size_penalty_ratio)))`
- [X] T018 [US3] Update `GET /api/render-predictions` in `app.py` to retrieve `duration_s` from queue items and calculate scaled estimates
- [X] T019 [US3] Update client prediction badge renderer in `templates/index.html` to consume and display scaled predictions and total queue ETA

**Checkpoint**: User Stories 1, 2, and 3 are all functional and testable independently.

---

## Phase 6: User Story 4 - Robust Non-Destructive Refresh & Timeline Finalization Fidelity (Priority: P4)

**Goal**: Replace disruptive `location.reload()` with asynchronous queue sync preserving active renders and appending new files, and ensure Step 6 checkmark is reliably displayed upon video completion.

**Independent Test**: Click "Làm Mới" while batch render is running; verify page does not reload, ongoing render continues uninterrupted, newly added files are appended to queue, and scroll remains locked to active row. Complete video render and verify all 6 timeline steps display green checkmarks.

### Implementation for User Story 4

- [X] T020 [P] [US4] Implement endpoint `POST /api/refresh-queue` in `app.py` that scans video folder, preserves existing queue items and active render states, appends newly discovered files, and returns `{ success: true, queue, new_items_added, active_item_id }`
- [X] T021 [US4] Implement asynchronous `refreshQueueState()` function in `templates/index.html` replacing `location.reload()`, updating queue data, preserving active render state, and re-scrolling to active row
- [X] T022 [US4] Add debouncing and in-flight guard to "Làm Mới" button in `templates/index.html` to prevent multiple concurrent sync requests
- [X] T023 [US4] Fix timeline step 6 checkmark race condition in `templates/index.html` by explicitly applying `step-completed` class with checkmark icon to all 6 steps upon receiving render completion `data.success: true`

**Checkpoint**: All 4 user stories are fully implemented and integrated.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Constitution compliance check, documentation update, and full end-to-end verification.

- [X] T024 [P] Verify Constitution compliance (Principles I to V) across all changes in `app.py`, `services/telemetry_manager.py`, and `templates/index.html`
- [X] T025 Execute end-to-end quickstart scenarios in `specs/003-queue-ux-and-modal-picker/quickstart.md` across all 8 user requirements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — executes immediately.
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**.
- **User Stories (Phase 3+)**: Depend on Foundational phase completion.
  - Can execute sequentially in priority order (`P1` → `P2` → `P3` → `P4`).
  - Or in parallel across independent files (`app.py` backend vs `templates/index.html` frontend).
- **Polish (Phase 7)**: Depends on all user stories completing.

### User Story Dependencies

- **US1 (P1)**: Operates primarily in `templates/index.html` (CSS, scroll logic, compact bar). No dependency on other stories.
- **US2 (P2)**: Operates in `templates/index.html` (`#mediaModal`, carousel). Depends on existing `/api/update-queue`. Independent of US3/US4.
- **US3 (P3)**: Operates in `app.py` and `services/telemetry_manager.py` (probed duration, scaled formula). Independent of US1/US2.
- **US4 (P4)**: Operates in `app.py` (refresh-queue) and `templates/index.html` (async refresh, step 6 fix). Independent of US1/US2/US3.

---

## Parallel Execution Opportunities

```bash
# Parallel Track 1 (Frontend Layout & Modal - US1 & US2):
Task T005: "Add CSS styles for collapsed setup summary bar in templates/index.html"
Task T011: "Implement HTML markup and CSS styling for #mediaModal in templates/index.html"

# Parallel Track 2 (Backend Probing & Telemetry - US3 & US4):
Task T015: "Implement fast video duration probe helper in app.py"
Task T017: "Update predict_duration in services/telemetry_manager.py"
Task T020: "Implement endpoint POST /api/refresh-queue in app.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (`T001` - `T002`).
2. Complete Phase 2: Foundational (`T003` - `T004`).
3. Complete Phase 3: User Story 1 (`T005` - `T009`).
4. **STOP and VALIDATE**: Verify setup collapse, clean Column 1, sticky scroll alignment, and row locking.

### Incremental Delivery

1. Setup + Foundational → Core types and parameters ready.
2. User Story 1 (P1) → Viewport and auto-scroll fixed (MVP!).
3. User Story 2 (P2) → Interactive modal image picker replacing table dropdown.
4. User Story 3 (P3) → Real-duration duration estimation scaling.
5. User Story 4 (P4) → Non-destructive reload and reliable Step 6 checkmark.
6. Polish → End-to-end verification and Constitution sign-off.

---

## Notes

- All tasks use strict checklist format `- [ ] [TaskID] [P?] [Story?] Description with file path`.
- Tasks reference exact file paths (`app.py`, `services/telemetry_manager.py`, `templates/index.html`).
- State mutations are defensive and compliant with Constitution Principle III (Fail-Safe Media).

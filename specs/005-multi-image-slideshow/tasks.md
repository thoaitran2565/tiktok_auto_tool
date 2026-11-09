# Tasks: Multi-Image Video Slideshow with Smooth Transitions

**Input**: Design documents from `/specs/005-multi-image-slideshow/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Organization**: Tasks are grouped by foundational prerequisites and user stories to enable independent implementation and testing.

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Clear action and exact file path in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize multi-image schema defaults and state definitions

- [X] T001 Initialize multi-image attributes (`is_multi_image`, `image_count`, `image_list`) in `services/queue_service.py`

---

## Phase 2: Foundational (Backend Services & APIs)

**Purpose**: Build standalone domain service modules and endpoints that power multi-image workflows

- [X] T002 [P] Implement `ScannerService.get_random_images_batch()` in `services/scanner_service.py` to sample $N$ distinct random images from the active image repository
- [X] T003 [P] Implement `SlideshowService` with right-to-left horizontal slide animation in `services/slideshow_service.py` per `contracts/multi-image-api-contract.md`
- [X] T004 Implement multi-image mutation methods (`toggle_multi_image`, `update_multi_image_count`, `set_multi_image_list`) in `services/queue_service.py`
- [X] T005 Expose `POST /api/random-images-batch` and extend `POST /api/update-queue` in `app.py` per `contracts/multi-image-api-contract.md`

**Checkpoint**: Core multi-image backend services and API contracts ready for frontend binding and rendering integration.

---

## Phase 3: User Story 1 - Per-Video Multi-Image Toggle & Count Configuration (Priority: P1)

**Goal**: Provide creators with per-video toggle switches and stepper controls (`-`/`+`) in the queue table to configure multi-image mode.

**Independent Test**: Load folders into the queue, toggle "Nhiều ảnh" switch ON for a video item, verify count defaults to 10 images, click `+` and `-` to adjust count, and refresh the queue to confirm state persistence.

### Implementation for User Story 1

- [X] T006 [US1] Add CSS styles for toggle switches, count steppers, and multi-image badges in `templates/index.html`
- [X] T007 [US1] Update Column 2 in `renderQueueTable()` to display the multi-image toggle switch, single-image thumbnail, and stepper controls in `templates/index.html`
- [X] T008 [US1] Implement client-side toggle handler `toggleMultiImageMode(id)` and count adjustment handler `adjustImageCount(id, delta)` in `templates/index.html`

**Checkpoint**: User Story 1 operational. Creators can toggle and adjust image counts for each video in the queue.

---

## Phase 4: User Story 2 - Smooth Right-to-Left Slide Transition Slideshow Rendering Engine (Priority: P1)

**Goal**: Render vertical 9:16 videos with smooth right-to-left horizontal slide transitions between sequential images matching total audio duration.

**Independent Test**: Render a video with multi-image mode enabled (e.g. 5 images on a 30s video), play the resulting MP4, and verify smooth slide-in motion at 1080x1920 with intact lyrics and logo overlays.

### Implementation for User Story 2

- [X] T009 [US2] Integrate `SlideshowService.create_slideshow_clip()` into `services/render_pipeline.py` stage 4 (`visual_generation`) when `is_multi_image` is enabled
- [X] T010 [US2] Ensure standard 9:16 vertical formatting, 20% background dimming, and stable overlay compositing in `services/slideshow_service.py` and `services/render_pipeline.py` per Constitution Principle II

**Checkpoint**: User Story 2 operational. Multi-image videos render with smooth right-to-left slide transitions and full visual fidelity.

---

## Phase 5: User Story 3 - Multi-Image Thumbnail Gallery, Individual Swap, and Re-roll Controls in Modal (Priority: P2)

**Goal**: Allow creators to inspect the ordered multi-image gallery in a modal dialog, swap individual photos, delete slots, or re-roll the entire batch with one click.

**Independent Test**: Open the curation modal for a multi-image video item, inspect the gallery grid, click "Đổi ngẫu nhiên bộ ảnh" to re-roll, swap an individual slot's image, and confirm the updated list.

### Implementation for User Story 3

- [X] T011 [US3] Add modal view `openMultiImagePickerModal(itemId)` and gallery slot grid rendering in `templates/index.html`
- [X] T012 [US3] Implement slot image replacement, slot deletion, and full batch re-roll handler `rerollMultiImageBatch(itemId)` in `templates/index.html`

**Checkpoint**: User Story 3 operational. Complete multi-image curation and inspection in modal.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Syntax verification, regression testing, and end-to-end scenario validation

- [X] T013 [P] Verify Python syntax and import integrity across all service modules and `app.py` via `python -m py_compile`
- [X] T014 Execute full validation scenarios against `specs/005-multi-image-slideshow/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1; blocks User Stories 1, 2, and 3.
- **User Story 1 (Phase 3)**: Depends on Phase 2; updates frontend queue table.
- **User Story 2 (Phase 4)**: Depends on Phase 2 (`slideshow_service.py`) and User Story 1 (`is_multi_image` flag).
- **User Story 3 (Phase 5)**: Depends on Phase 2 and User Story 1; enriches modal curation.
- **Polish (Phase 6)**: Runs after all user story phases complete.

### Parallel Opportunities

- `T002` (`scanner_service.py`) and `T003` (`slideshow_service.py`) can run in parallel.
- `T006` (CSS styling) can run in parallel with backend foundational tasks.
- `T013` (syntax check) can run independently in parallel.

---

## Implementation Strategy

### MVP Scope (User Story 1 & User Story 2)
1. Complete Phase 1 & 2: Setup multi-image attributes, batch random sampling, `SlideshowService`, and API endpoints.
2. Complete Phase 3: Add toggle switch and count steppers to the queue table in `templates/index.html`.
3. Complete Phase 4: Integrate `SlideshowService` into `render_pipeline.py` and verify right-to-left slide rendering.
4. Validate MVP: Toggle multi-image on a video, adjust count, render, and inspect export.
5. Complete Phase 5: Add multi-image curation modal with individual slot swap and batch re-roll.
6. Complete Phase 6: Run full quickstart validation scenarios.


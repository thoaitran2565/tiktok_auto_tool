# Tasks: Lyrics Testing Page (/test)

**Input**: Design documents from `/specs/007-lyrics-test-page/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Organization**: Tasks are grouped by foundational prerequisites and user stories to enable independent implementation and testing.

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Clear action and exact file path in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Register `/test` route and navigation links across the application.

- [X] T001 Register route `GET /test` in `app.py` rendering `templates/test.html`
- [X] T002 [P] Add navigation link to `/test` in header actions of `templates/index.html` and `templates/manage.html`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend endpoints for video scanning and isolated lyrics extraction.

**⚠️ CRITICAL**: Must complete before user stories to ensure frontend can scan videos and trigger tests.

- [X] T003 Implement backend endpoint `POST /api/test-scan-videos` in `app.py` scanning video files via `ScannerService.scan_videos()` per `contracts/test-api-contract.md`
- [X] T004 Implement backend endpoint `POST /api/test-lyrics` in `app.py` executing audio extraction, `extract_raw_lyrics()`, `clean_lyrics_with_ai()`, and defensive scratch audio cleanup in a `finally` block per `contracts/test-api-contract.md`

**Checkpoint**: Backend test APIs ready for frontend consumption.

---

## Phase 3: User Story 1 - Dedicated Lyrics Testing Interface at /test (Priority: P1) 🎯 MVP

**Goal**: Deliver a dedicated testing page at `/test` where users can scan video directories and test lyrics for individual videos without video encoding.

**Independent Test**: Navigate to `http://127.0.0.1:5000/test`. Scan a video directory, click "Test Lyrics" on a video, and verify row updates to `Hoàn thành` displaying detected song title and badge with 0 MB MP4 files generated.

### Implementation for User Story 1

- [X] T005 [US1] Create `templates/test.html` with dark UI layout, navigation bar, and streamlined video-only setup toolbar (omitting image folder input)
- [X] T006 [US1] Implement video queue table rendering in `templates/test.html` displaying video name, duration, size, and test status badge
- [X] T007 [US1] Implement single-item test execution logic in `templates/test.html` sending `POST /api/test-lyrics` and dynamically updating row state upon completion

**Checkpoint**: User Story 1 operational. Users can scan videos and test individual video lyrics at `/test`.

---

## Phase 4: User Story 2 - Side-by-Side Lyrics Comparison & Inspection (Priority: P1)

**Goal**: Provide an interactive inspection modal allowing users to compare raw Whisper transcripts and AI-cleaned lyrics side-by-side with copy-to-clipboard functionality.

**Independent Test**: On a tested item, click "Xem Lyrics". Verify modal displays two distinct columns (Raw Whisper vs AI Refined), song title header, source badge (`AI` vs `Original`), and test copy buttons.

### Implementation for User Story 2

- [X] T008 [US2] Create responsive side-by-side lyrics comparison modal markup and styles in `templates/test.html`
- [X] T009 [US2] Implement modal population logic, title and source badge binding, and copy-to-clipboard handlers in `templates/test.html`

**Checkpoint**: User Story 2 operational. Lyrics quality and AI cleaning can be compared and copied with one click.

---

## Phase 5: User Story 3 - Batch Lyrics Testing across Queue (Priority: P2)

**Goal**: Support batch testing across the entire video queue with start and stop controls and live progress tracking.

**Independent Test**: Queue 3+ videos on `/test` and click "Bắt Đầu Test Tất Cả". Verify videos are processed sequentially with live status indicators, and clicking "Dừng Lại" cleanly pauses execution.

### Implementation for User Story 3

- [X] T010 [US3] Add "Bắt Đầu Test Tất Cả" và "Dừng Lại" buttons to header action bar in `templates/test.html`
- [X] T011 [US3] Implement sequential batch queue loop in `templates/test.html` with real-time status updates and abort flag handling

**Checkpoint**: User Story 3 operational. Entire folders can be batch tested rapidly.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Syntax verification, regression testing, and end-to-end scenario validation.

- [X] T012 [P] Verify Python syntax and endpoint integrity in `app.py` via `python -m py_compile`
- [X] T013 Execute full validation scenarios against `specs/007-lyrics-test-page/quickstart.md` verifying 0 MB video output and sub-10s test completion

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - starts immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - BLOCKS all user stories
- **User Story 1 (Phase 3 - P1)**: Depends on Phase 2 - delivers primary MVP testing capability
- **User Story 2 (Phase 4 - P1)**: Depends on User Story 1 - enables detailed lyrics comparison modal
- **User Story 3 (Phase 5 - P2)**: Depends on User Story 1 & 2 - adds automated batch queue execution
- **Polish (Phase 6)**: Runs after all user stories complete

### Parallel Opportunities

- `T001` and `T002` can run in parallel
- `T003` and `T004` can run in parallel
- `T012` runs in parallel with manual validation

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Setup) and Phase 2 (Foundational)
2. Complete Phase 3 (User Story 1: Basic `/test` page + single video test)
3. **Validate**: Test 1 video on `/test` and verify lyrics extraction in ~5–10s with zero video output!

### Incremental Delivery
1. Add User Story 2 (Side-by-side comparison modal + copy buttons)
2. Add User Story 3 (Batch test execution loop)
3. Run complete quickstart validation suite

# Feature Specification: Modal Image Wheel Zoom & Application Logic Decoupling

**Feature Branch**: `004-modal-zoom-and-modularization`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Thêm tính năng cuộc chuột vào ảnh trong model xem ảnh để phòng to ảnh. Tách code xử lý ra khỏi app.py"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interactive Mouse Wheel Zoom & Pan in Image Modals (Priority: P1)

As a content creator inspecting candidate or source images before rendering, I want to scroll my mouse wheel over the image in the modal viewer to zoom in and examine fine visual details (such as facial focus, resolution artifacts, or text legibility), and zoom out smoothly without the background page scrolling or the layout breaking.

**Why this priority**: Directly impacts the core curation experience. High-resolution images often appear scaled down in modal stages, preventing users from checking visual quality without downloading or opening external apps.

**Independent Test**: Open any image in either the sample image swap modal or the lightbox viewer, position the cursor over the image, and scroll the mouse wheel up. Verify that the image smoothly scales up around the cursor/center, bounds between 1.0x and 5.0x, allows panning when enlarged, and resets cleanly on double-click or modal close.

**Acceptance Scenarios**:

1. **Given** an open image viewer modal displaying a source or candidate image, **When** the user scrolls the mouse wheel upward over the image, **Then** the image enlarges smoothly up to a maximum safe threshold (5.0x) without scrolling the underlying web page.
2. **Given** an enlarged image in the modal (> 1.0x scale), **When** the user scrolls the mouse wheel downward, **Then** the image smoothly shrinks back down to its original fit (minimum 1.0x).
3. **Given** an enlarged image, **When** the user clicks and drags the image (pan), **Then** the image moves intuitively to follow the cursor within container boundaries.
4. **Given** an enlarged image or adjusted view, **When** the user double-clicks the image or selects a new candidate image, **Then** the zoom scale and offset immediately reset to their default 1.0x baseline.

---

### User Story 2 - Decoupled Core Media & Queue Services from Routing Layer (Priority: P1)

As a maintainer and developer of the application, I want core business logic (queue management, lazy folder scanning, video duration estimation, and configuration persistence) to be cleanly extracted from the primary HTTP routing file into dedicated domain service modules, so that the code remains modular, maintainable, testable, and compliant with Constitution Principle I.

**Why this priority**: Essential architectural hygiene. The primary HTTP routing file has become overly dense by hosting scanning routines, queue mutations, duration estimation, and configuration I/O alongside web endpoints, increasing risk of regression and violating separation of concerns.

**Independent Test**: Execute full end-to-end operational flows (folder scanning, random image selection, queue updates, batch rendering, and telemetry inspection) and verify that all operations complete identically with 100% functional parity while the primary routing entrypoint only dispatches calls to modular domain services.

**Acceptance Scenarios**:

1. **Given** a request to scan directories or retrieve folder configurations, **When** the system processes the request, **Then** dedicated scanning and configuration service modules perform the file system inspection and return structured domain models to the router.
2. **Given** a request to modify or refresh the render queue, **When** the queue mutation is requested, **Then** a dedicated queue service module handles queue synchronization, duration estimations, and lock states independently of the HTTP presentation layer.
3. **Given** unit or integration test harnesses, **When** testing folder scanning or queue management logic, **Then** these modules can be imported and executed standalone without launching a web server.

---

### User Story 3 - Visual Feedback and Zoom Controls in Modal Viewer (Priority: P2)

As a content creator inspecting images, I want visual feedback showing the current zoom level and quick reset controls in the modal viewer, so that I always know the magnification level and can return to normal view with a single click.

**Why this priority**: Enhances usability and accessibility by providing explicit visual status and alternate interaction mechanisms for users who prefer button clicks over mouse gestures.

**Independent Test**: Zoom in using mouse wheel and verify that a non-intrusive zoom badge (e.g. `150%`, `200%`) displays the current zoom level, and clicking a reset button or double-clicking restores normal view.

**Acceptance Scenarios**:

1. **Given** an image zoomed past 1.0x, **When** the scale changes, **Then** a subtle overlay badge indicates the current zoom percentage.
2. **Given** an image at any zoom level above 1.0x, **When** the user clicks a dedicated reset zoom control or switches to another thumbnail, **Then** the image smoothly transitions back to 100% fit and the badge disappears or resets.

---

### Edge Cases

- **Trackpad pinch vs. mouse wheel**: How does the system handle high-frequency trackpad wheel events without runaway zooming? The zooming handler must throttle or dampen delta steps for predictable incrementing.
- **Image boundary clipping**: What happens when an enlarged image is panned? Panning translation must clamp so the image does not disappear entirely out of the viewport.
- **Modal switching while zoomed**: If an image is zoomed to 300% and the user clicks another thumbnail in the carousel or closes the modal, the zoom state must cleanly reset to 100% without retaining previous offsets.
- **Large directory handling during service decoupling**: Decoupled service modules must strictly preserve lazy iterator limits (<60 images) and instantaneous duration heuristics (<0.05s response times) without regressing to blocking scans.
- **Missing or unreadable configuration**: Configuration service must gracefully return fallback defaults if the persistent config file is missing or contains malformed JSON.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The modal image viewer MUST support smooth mouse wheel zoom in and zoom out when scrolling over the displayed preview image.
- **FR-002**: Mouse wheel zooming MUST be bounded between a minimum of 1.0x (container fit) and a maximum of 5.0x magnification.
- **FR-003**: Scrolling over the modal image MUST prevent the default browser window/page scrolling action.
- **FR-004**: Users MUST be able to click and drag (pan) an enlarged image (> 1.0x) within the modal viewport to examine different areas.
- **FR-005**: Double-clicking an enlarged image MUST reset its zoom level and panning position back to 1.0x centered fit.
- **FR-006**: Switching candidate images via thumbnail selection, clicking "Chọn ngẫu nhiên", or closing the modal MUST automatically reset zoom and pan transforms to default.
- **FR-007**: Core folder scanning and media discovery logic MUST reside in a dedicated media discovery service outside the primary HTTP routing file.
- **FR-008**: Queue synchronization, item locking, and queue state mutation logic MUST reside in a dedicated queue management service outside the primary HTTP routing file.
- **FR-009**: Configuration reading and writing MUST reside in a dedicated configuration service outside the primary HTTP routing file.
- **FR-010**: The primary application file (`app.py`) MUST act strictly as an HTTP controller/orchestration layer that delegates business logic to specialized services.
- **FR-011**: All existing API routes, contracts, and frontend behaviors MUST maintain 100% backwards compatibility and zero performance regression.

### Key Entities

- **Modal Zoom State**: Represents the active client-side view transformation on an image (scale factor, horizontal translation, vertical translation, is-dragging flag, drag origin coordinates).
- **Queue State Service**: Represents the domain component managing in-memory session queues, video item states, locking flags, and persistence sync.
- **Scanner Service**: Represents the domain component responsible for non-blocking directory discovery, sample image extraction, and video metadata inspection.
- **Config Service**: Represents the component managing loading, validating, and saving persistent user directory preferences.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can zoom from 1.0x to 5.0x and pan smoothly across modal images with 60 FPS responsiveness and zero page scroll leakage.
- **SC-002**: Switching candidate images or closing the modal resets zoom transform in under 50 milliseconds.
- **SC-003**: The primary application file (`app.py`) is streamlined to less than 280 lines of clean HTTP route definitions, with all domain operations delegated to modular services.
- **SC-004**: 100% of existing API endpoints (`/api/load-folders`, `/api/refresh-queue`, `/api/update-queue`, `/api/random-image`, `/api/render-single`) maintain full functional parity and response speed (<0.05s for discovery and queue synchronization).

## Assumptions

- Target users use modern desktop browsers (Chrome, Edge, Firefox) equipped with a standard mouse wheel or trackpad.
- Touch gesture zoom (pinch-to-zoom on mobile) is out of scope for this desktop-focused workflow tool.
- Service decoupling will utilize Python standard modular packaging under the existing `services/` namespace directory.
- In-memory session queue data structures will maintain the established dictionary schema to ensure frontend compatibility.


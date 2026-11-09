# Feature Specification: Multi-Image Video Slideshow with Smooth Transitions

**Feature Branch**: `005-multi-image-slideshow`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Thêm tính năng tạo video nhiều ảnh: Thêm công tắc bật/tắt tính năng này cho mỗi video; Khi bật sẽ lấy ngẫu nhiên 10 ảnh và có thể tăng giảm số lượng tùy ý; chuyển động mượt mà qua lại giữa nhiều ảnh"

## Clarifications

### Session 2026-11-04
- Q: Bạn muốn hiệu ứng chuyển động mượt mà giữa các ảnh theo phong cách nào? → A: Trượt ngang từ phải sang trái (Slide from right to left)
- Q: Bạn có cần tính năng can thiệp/chỉnh sửa từng ảnh lẻ trong danh sách nhiều ảnh không? → A: Hỗ trợ cả 2 - Đổi ngẫu nhiên toàn bộ bộ ảnh và click vào từng ảnh để đổi hoặc xóa lẻ trong modal.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Per-Video Multi-Image Toggle & Count Configuration in Queue (Priority: P1)

As a creator configuring a batch of videos, I want an intuitive toggle for each item in the render queue to switch between single-image mode and multi-image slideshow mode, and when enabled, automatically select a random set of 10 images with controls to easily increment or decrement the count, so that I can customize visual variety for each video individually without extra setup steps.

**Why this priority**: Essential UI entrypoint and configuration mechanism requested directly by the user. Enables creators to decide on a per-video basis whether a video uses a single static background or a dynamic multi-image slideshow.

**Independent Test**: Load folders into the queue, toggle the "Ghép nhiều ảnh" switch ON for a video item. Verify that 10 random images are immediately assigned, a count stepper (`-` / `+`) appears allowing adjustment between 2 and the total available images, and toggling OFF restores single-image mode.

**Acceptance Scenarios**:

1. **Given** a queue item in single-image mode, **When** the user activates the multi-image toggle, **Then** the item switches to multi-image mode, automatically chooses 10 distinct random images from the loaded image folder, and displays a count indicator (`10 ảnh`).
2. **Given** an item with multi-image mode enabled, **When** the user clicks the increment (`+`) or decrement (`-`) buttons or enters a number, **Then** the image count updates immediately, adding new random images or trimming the list accordingly (bounded between 2 and the total available images).
3. **Given** an item with multi-image mode enabled, **When** the user deactivates the toggle, **Then** the item gracefully reverts to single-image mode using the primary image thumbnail.
4. **Given** queue state refreshes or browser reloads, **When** `/api/refresh-queue` or state sync runs, **Then** the multi-image toggle state and custom image list are non-destructively preserved.

---

### User Story 2 - Smooth Right-to-Left Slide Transition Slideshow Rendering Engine (Priority: P1)

As a creator watching the rendered video, I want the multi-image background to smoothly transition between consecutive images using a clean right-to-left horizontal slide motion (ảnh sau trượt từ phải sang trái), with durations automatically synchronized to match the total video length, so that the final output looks dynamic and engaging for TikTok and Shorts.

**Why this priority**: Core video quality requirement. Smooth visual motion between slides is the primary aesthetic differentiator requested ("chuyển động mượt mà qua lại giữa nhiều ảnh").

**Independent Test**: Render a video with multi-image mode enabled (e.g. 5 images on a 30s video). Inspect the exported video file and verify that each image transitions into the next with a smooth 0.6s–0.8s right-to-left slide animation, no frame freezes or black glitches occur, and the total visual timeline aligns perfectly with the audio track.

**Acceptance Scenarios**:

1. **Given** a video queue item configured with $N$ images ($N \ge 2$) and duration $D$, **When** the rendering pipeline executes the visual generation and compositing stages, **Then** it generates an image sequence where each slide displays for $D / N$ seconds with a smooth right-to-left horizontal slide transition into the subsequent image.
2. **Given** images of varying original aspect ratios and dimensions, **When** composited into the vertical slideshow, **Then** each image is scaled and centered to strictly maintain 9:16 vertical formatting (`1080x1920`) without distortion or stretching per Constitution Principle II.
3. **Given** a multi-image video with lyrics and logo overlays, **When** composited, **Then** the text overlays, background dimming, and upper-corner logo remain steady and legible across all image transitions.

---

### User Story 3 - Multi-Image Thumbnail Gallery, Individual Swap, and Re-roll Controls in Modal (Priority: P2)

As a creator inspecting the multi-image selection, I want to view the gallery of chosen images in the modal dialog, click on any individual image slot to replace or remove it, and re-roll the entire random selection with one click, so that I have full creative confidence before starting a long batch render.

**Why this priority**: Enhances curation confidence and quality control, allowing users to verify which photos will appear in the slideshow and make granular adjustments.

**Independent Test**: Open the curation modal for a multi-image video item, verify that all assigned images appear in a gallery grid/strip, click a single image slot to replace it with another photo from the folder, and click "Đổi ngẫu nhiên bộ ảnh" to replace the entire set.

**Acceptance Scenarios**:

1. **Given** an item in multi-image mode, **When** the user clicks the thumbnail area or edit button, **Then** the modal displays the active slideshow sequence as an ordered thumbnail gallery with slot numbers (1, 2, 3...).
2. **Given** the multi-image modal viewer, **When** the user clicks an individual image slot, **Then** they can choose a replacement image from the folder carousel or delete that specific slot (decrementing the count).
3. **Given** the multi-image modal viewer, **When** the user clicks "Đổi ngẫu nhiên bộ ảnh", **Then** the current selection is replaced with a fresh random batch matching the active count.

---

### Edge Cases

- **Folder contains fewer images than requested**: If the user sets the count to 10 but the image folder only contains 6 images, the system must gracefully limit the selection to 6 without errors, or loop the available set smoothly.
- **Very short video with high image count**: For a 10-second video with 15 images, per-slide display time drops below 1 second. The system should adjust transition duration dynamically (e.g. `min(0.8, slide_duration * 0.3)`) to prevent overlapping crossfades from colliding.
- **Single image folder**: If the image folder has only 1 image, the multi-image toggle should warn the user or auto-fallback to single image mode.
- **Memory footprint during batch encoding**: Compositing many high-resolution images simultaneously could spike RAM. The video pipeline must handle image sequencing incrementally and release memory safely.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each video queue item MUST feature an interactive toggle switch to enable or disable multi-image mode.
- **FR-002**: Enabling multi-image mode MUST default to selecting 10 random images from the active image repository.
- **FR-003**: Each multi-image queue item MUST provide user controls (stepper `-`/`+` and/or direct numeric input) to increase or decrease the image count between a minimum of 2 and a maximum bounded by folder capacity (up to 50).
- **FR-004**: Adjusting image count MUST automatically update the assigned image list in the queue state in real time.
- **FR-005**: The render pipeline MUST detect multi-image mode on each queue item and construct a synchronized video slideshow matching the exact audio duration.
- **FR-006**: Transitions between adjacent images in the slideshow MUST use smooth right-to-left horizontal slide animations (trượt từ phải sang trái) with duration scaled to slide length (typically 0.6s to 0.8s).
- **FR-007**: Multi-image slideshow clips MUST strictly adhere to 9:16 vertical resolution (`1080x1920`) without stretching or distortion.
- **FR-008**: Dimming overlays, logo placement, and lyrics typography MUST be composited seamlessly on top of the dynamic slideshow background.
- **FR-009**: The queue state synchronization (`/api/refresh-queue`) and item update API (`/api/update-queue`) MUST persist and preserve multi-image configuration parameters (`is_multi_image`, `image_count`, `image_list`).
- **FR-010**: Users MUST be able to re-roll the entire random image batch for any multi-image item with a single click.
- **FR-011**: Users MUST be able to inspect the multi-image gallery in the modal, click any individual image slot to replace it with a different image from the folder, or remove it from the slideshow sequence.

### Key Entities

- **Queue Item Multi-Image Metadata**:
  - `is_multi_image`: `boolean` (default: `false`).
  - `image_count`: `integer` (default: `10`, range: `2` to `50`).
  - `image_list`: `List[str]` (ordered list of image filenames selected for the slideshow).
- **Slideshow Transition Spec**:
  - `transition_type`: `str` (`slide_left` right-to-left horizontal slide).
  - `slide_duration`: `float` (seconds each image remains on screen).
  - `transition_duration`: `float` (slide animation overlap time, typically `0.6s` to `0.8s`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Creators can toggle multi-image mode and adjust the image count for any video in under 3 seconds with immediate UI responsiveness.
- **SC-002**: Multi-image video rendering produces seamless right-to-left slide transitions with zero frame stutter, black flashes, or audio-video desynchronization.
- **SC-003**: 100% of rendered multi-image videos output at exact `1080x1920` resolution with uncompromised lyrics readability.
- **SC-004**: Queue state persistence maintains complete fidelity across browser refreshes and non-destructive queue reload operations.

## Assumptions

- Source images are located in the user's configured image folder.
- Standard cross-dissolve transition provides the optimal balance of elegance, performance, and compatibility across diverse image types.
- The default count of 10 images provides an ideal pace (approx. 3-4 seconds per slide for a standard 30-40 second short-form song).


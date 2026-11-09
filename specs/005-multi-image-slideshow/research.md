# Phase 0: Research & Technical Decisions

**Feature**: Multi-Image Video Slideshow with Smooth Transitions  
**Date**: 2026-11-04  
**Branch**: `005-multi-image-slideshow`  

## 1. Slide Transition Technique in MoviePy 2.0

### Decision
Implement a specialized right-to-left slide animation using MoviePy 2.0's coordinate position functions (`with_position`) within a `CompositeVideoClip` layer stack, encapsulated in a new standalone module `services/slideshow_service.py`.

### Technical Architecture
- **Timeline Calculation**:
  - Let total video duration be $D$, number of images be $N$.
  - Per-slide interval: $\Delta t = D / N$.
  - Transition duration: $T_{trans} = \min(0.7, \Delta t \times 0.25)$ seconds (e.g. 0.6s).
  - Slide $0$ starts at $t=0$, positioned statically at $(0, 0)$ for duration $D$.
  - Slide $i$ ($1 \le i < N$) starts at $t_i = i \times \Delta t - T_{trans}$.
  - During the transition interval $[0, T_{trans}]$, slide $i$ animates horizontally:
    $$x(t) = \text{round}\left(1080 \times \left(1 - \frac{t}{T_{trans}}\right)\right)$$
    moving smoothly from $x=1080$ (offscreen right) to $x=0$ (fully visible).
  - For $t > T_{trans}$, slide $i$ stays at $(0, 0)$ until the end of the video or until covered by slide $i+1$.
- **Pre-Processing for Zero Distortion**:
  - Each source image is loaded with Pillow (`PIL.Image`) and fitted to $1080 \times 1920$ vertical canvas:
    - Center-cropped or letterboxed with black/blurred matting to preserve native aspect ratio (Constitution Principle II).
    - Reduced brightness by 20% to maintain text contrast (Constitution Principle II).
  - Converted to numpy array and passed into MoviePy `ImageClip`.

### Rationale
- **Butter-Smooth Motion**: Position-based slide translation creates a crisp, professional TikTok/Reels carousel effect.
- **Robust Layering**: Because slide $i+1$ enters on a higher layer, it naturally glides over slide $i$ with zero visual tearing or black gaps.
- **Resource Safety**: Pre-scaling with Pillow in memory is orders of magnitude faster than MoviePy resizing filters and prevents CPU spikes.

### Alternatives Considered
- *FFmpeg complex filtergraphs (`xfade=transition=slideleft`)*: Rejected because chaining dynamic numbers of inputs (2 to 50 images) in raw FFmpeg CLI strings is error-prone, fragile across different platforms, and hard to inspect programmatically.
- *Native crossfade only*: Rejected because the user explicitly specified horizontal slide motion ("trượt từ phải sang trái").

---

## 2. Queue State Schema & Curation UX

### Decision
Extend `QueueItem` with three optional fields:
- `is_multi_image`: `bool` (default: `False`).
- `image_count`: `int` (default: `10`, clamped between `2` and `50`).
- `image_list`: `List[str]` (ordered list of selected filenames).

### UI Controls in `templates/index.html` (Column 2)
1. **Compact Mode Switch**: A clean toggle switch `[Ghép nhiều ảnh]` in column 2.
2. **Stepper Controls**: When toggled ON, shows `[-] 10 ảnh [+]` and a dynamic preview badge (`🎬 10 ảnh`).
3. **Modal Curation Enhancement**:
   - In single-image mode: standard candidate picker modal.
   - In multi-image mode: modal displays the ordered gallery of all $N$ assigned images with slot numbers (1 to $N$).
   - Top action: "Đổi ngẫu nhiên bộ ảnh" (re-rolls the entire batch).
   - Slot actions: clicking any slot allows picking an alternate image from the carousel or removing that slot.

### Rationale
- Completely non-breaking for existing single-image users.
- Intuitive, low-friction entry point directly in the queue table.
- Preserved across non-destructive queue refreshes via `QueueService`.


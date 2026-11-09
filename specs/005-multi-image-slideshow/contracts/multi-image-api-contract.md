# Interface Contract: Multi-Image API & Backend Services

**Feature**: Multi-Image Video Slideshow with Smooth Transitions  
**Date**: 2026-11-04  
**Scope**: Python Services & HTTP API Contracts  

## 1. `POST /api/update-queue` (Extended Schema)

Accepts multi-image configuration updates in addition to single image swapping:

### Request Body:
```json
{
  "id": 0,
  "image_name": "photo_01.jpg",
  "is_multi_image": true,
  "image_count": 10,
  "image_list": ["img1.jpg", "img2.jpg", "img3.jpg", "..."]
}
```

### Response:
```json
{
  "success": true,
  "item": {
    "id": 0,
    "is_multi_image": true,
    "image_count": 10,
    "image_list": ["img1.jpg", "img2.jpg", "..."]
  }
}
```

---

## 2. `POST /api/random-images-batch` (New Endpoint)

Generates a batch of distinct random images from the configured image directory:

### Request Body:
```json
{
  "count": 10,
  "exclude": ["optional_already_selected.jpg"]
}
```

### Response:
```json
{
  "success": true,
  "images": ["photo12.jpg", "photo45.jpg", "photo03.jpg", "..."]
}
```

---

## 3. `services/slideshow_service.py` (`SlideshowService`)

```python
class SlideshowService:
    @classmethod
    def create_slideshow_clip(
        cls,
        image_paths: List[str],
        total_duration: float,
        width: int = 1080,
        height: int = 1920,
        transition_duration: float = 0.65
    ) -> CompositeVideoClip:
        """
        Creates a 9:16 vertical video clip animating multiple images
        with right-to-left horizontal slide transitions.
        Strictly preserves aspect ratio and applies 20% background dimming.
        """
        ...
```

---

## 4. `services/render_pipeline.py` Integration

When executing stage 4 (`visual_generation`), `render_pipeline.render()` checks:
```python
if is_multi_image and len(image_list) >= 2:
    background_clip = SlideshowService.create_slideshow_clip(
        resolved_image_paths,
        video_duration,
        width=target_width,
        height=target_height
    )
else:
    background_clip = ImageClip(primary_image_array).with_duration(video_duration)
```
Logo and lyrics overlay clips are composited on top identically, ensuring 100% architectural and visual continuity.


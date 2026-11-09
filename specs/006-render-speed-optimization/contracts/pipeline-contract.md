# Interface Contract: Render Pipeline with Pre-Fetch Pipelining

**Feature**: `006-render-speed-optimization`  
**Date**: 2026-11-09  
**Scope**: Pipeline Orchestration (`services/render_pipeline.py`)  

---

## 1. Class: `RenderPipeline` Pipelining Contract

```python
class RenderPipeline:
    def pre_fetch_item(self, item_id: Any, video_path: str, image_path: str) -> Dict[str, Any]:
        """
        Executes Stages 1 to 4 asynchronously for the next queue item:
        - Stage 1: Audio extraction -> temp_audio_<id>.mp3
        - Stage 2: In-memory Whisper transcription
        - Stage 3: Gemini refinement (with 15s timeout guard)
        - Stage 4: Pillow 1080x1920 canvas generation -> temp_canvas_<id>.png
        
        Stores result in in-memory pre-fetch cache.
        """
        ...

    def render(
        self,
        item_id: Any,
        video_path: str,
        image_path: str,
        progress_callback: Optional[Callable[[str, str, Optional[str]], None]] = None,
        is_multi_image: bool = False,
        image_paths: Optional[List[str]] = None,
        next_item_to_prefetch: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        If item_id was pre-fetched, retrieves prepared canvas and audio immediately,
        skipping directly to Stage 5 (Media Encoding) in FFmpeg.
        
        Simultaneously triggers background pre_fetch_item() on next_item_to_prefetch.
        """
        ...
```

---

## 2. Telemetry Timing Rules

- When an item enters `render()` with pre-fetched artifacts, the recorded stage durations for Stages 1–4 reflect the actual background pre-fetch run time, ensuring accurate historical telemetry logs.
- Stage 5 records native FFmpeg encoding duration.


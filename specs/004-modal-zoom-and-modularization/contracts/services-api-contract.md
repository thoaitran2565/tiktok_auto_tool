# Interface Contract: Domain Services Architecture

**Feature**: Modal Image Wheel Zoom & Application Logic Decoupling  
**Date**: 2026-11-04  
**Scope**: Python Services Interface Contracts (`services/`)  

## 1. `services/config_service.py` (`ConfigService`)

```python
class ConfigService:
    CONFIG_FILE: str = 'config.json'

    @classmethod
    def load_config(cls) -> Dict[str, str]:
        """Loads and returns config dictionary with fallback defaults."""
        ...

    @classmethod
    def save_config(cls, image_folder: str, video_folder: str) -> None:
        """Persists image_folder and video_folder into config.json."""
        ...

    @classmethod
    def get_configured_folders(cls) -> Tuple[str, str]:
        """Returns (image_folder, video_folder)."""
        ...
```

---

## 2. `services/scanner_service.py` (`ScannerService`)

```python
class ScannerService:
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.webm')

    @classmethod
    def scan_sample_images(cls, img_folder: str, limit: int = 60) -> List[str]:
        """Lazy iterator via os.scandir collecting up to `limit` image names (<1ms)."""
        ...

    @classmethod
    def scan_videos(cls, vid_folder: str) -> List[Tuple[str, str, int]]:
        """Fast enumeration of video files returning (name, path, size_bytes) (<5ms)."""
        ...

    @classmethod
    def get_random_image(cls, img_folder: str) -> Optional[str]:
        """Returns a single random image filename from entire directory."""
        ...

    @classmethod
    def probe_single_video_duration(cls, video_path: str, default: float = 30.0) -> float:
        """Ultra-fast ffprobe video duration extraction with MoviePy fallback."""
        ...
```

---

## 3. `services/queue_service.py` (`QueueService`)

```python
class QueueService:
    @classmethod
    def init_queue_from_folders(cls, img_folder: str, vid_folder: str) -> Dict[str, Any]:
        """Discovers media and initializes full in-memory queue."""
        ...

    @classmethod
    def refresh_queue_state(cls) -> Dict[str, Any]:
        """Non-destructively synchronizes queue with directory contents."""
        ...

    @classmethod
    def update_item_image(cls, item_id: int, image_name: str) -> bool:
        """Updates paired image for a specific queue item."""
        ...

    @classmethod
    def get_queue(cls) -> List[Dict[str, Any]]:
        """Returns current in-memory queue representation."""
        ...

    @classmethod
    def get_item(cls, item_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves item by id."""
        ...

    @classmethod
    def set_session_folders(cls, img_folder: str, vid_folder: str) -> None:
        """Sets active session folders."""
        ...

    @classmethod
    def get_session_folders(cls) -> Tuple[str, str]:
        """Returns active (image_folder, video_folder)."""
        ...
```

---

## 4. `app.py` Controller Mapping

All existing Flask HTTP routes delegate directly to these services:
- `POST /api/load-folders` → `ConfigService.save_config()` + `QueueService.init_queue_from_folders()`
- `POST /api/refresh-queue` → `QueueService.refresh_queue_state()`
- `POST /api/update-queue` → `QueueService.update_item_image()`
- `GET /api/random-image` → `ScannerService.get_random_image()`
- `GET /api/get-config` → `ConfigService.load_config()`
- `POST /api/render-single` → delegates to `QueueService.get_item()` + `render_pipeline.render()`


# Phase 1: Data Model & Domain Entities

**Feature**: Modal Image Wheel Zoom & Application Logic Decoupling  
**Date**: 2026-11-04  
**Branch**: `004-modal-zoom-and-modularization`  

## 1. Client-Side Entities

### `ModalZoomState`
Tracks active transformation parameters and interaction state for zoomed preview images.

| Field | Type | Description | Default / Constraints |
|---|---|---|---|
| `scale` | `number` | Current magnification ratio | `1.0` (range: `1.0` to `5.0`) |
| `translateX` | `number` | Horizontal pixel offset from pan gesture | `0` |
| `translateY` | `number` | Vertical pixel offset from pan gesture | `0` |
| `isDragging` | `boolean` | Flag indicating active mouse drag pan | `false` |
| `startX` | `number` | Mouse clientX at start of drag | `0` |
| `startY` | `number` | Mouse clientY at start of drag | `0` |
| `minScale` | `number` | Minimum zoom threshold | `1.0` |
| `maxScale` | `number` | Maximum zoom threshold | `5.0` |

#### State Transitions:
- `RESET`: `scale = 1.0`, `translateX = 0`, `translateY = 0`, `isDragging = false`
- `WHEEL_ZOOM(delta)`: `scale = clamp(scale * factor, minScale, maxScale)`
- `DRAG_START(x, y)`: `if scale > 1.0: isDragging = true, startX = x - translateX, startY = y - translateY`
- `DRAG_MOVE(x, y)`: `if isDragging: translateX = x - startX, translateY = y - startY`
- `DRAG_END`: `isDragging = false`

---

## 2. Server-Side Domain Entities

### `AppConfig`
Managed by `services/config_service.py`.

| Field | Type | Description | Validation |
|---|---|---|---|
| `image_folder` | `str` | Absolute path to folder containing source images | Must be valid directory string |
| `video_folder` | `str` | Absolute path to folder containing source videos | Must be valid directory string |

### `ScannerResult`
Managed by `services/scanner_service.py`.

| Field | Type | Description |
|---|---|---|
| `sample_images` | `List[str]` | Up to 60 image filenames scanned via lazy iterator |
| `videos` | `List[Tuple[str, str, int]]` | Tuples of `(filename, full_path, size_bytes)` |

### `QueueItem`
Managed by `services/queue_service.py`.

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Sequential numeric identifier |
| `video_path` | `str` | Absolute filesystem path to source video |
| `video_name` | `str` | Base filename of source video |
| `duration_s` | `float` | Probed or estimated video duration in seconds |
| `size_mb` | `float` | File size in megabytes |
| `image_path` | `str` | Absolute filesystem path to paired image |
| `image_name` | `str` | Base filename of paired image |
| `status` | `str` | `Chờ render` \| `Đang render` \| `Hoàn thành` \| `Lỗi` |
| `output_file` | `str` | Filename of rendered output video |
| `output_folder` | `str` | `outputs` \| `outputs-no-lyrics` |
| `has_lyrics` | `bool` | Whether rendered output contains lyrics overlay |
| `is_locked` | `bool` | Whether item is protected from accidental modifications |


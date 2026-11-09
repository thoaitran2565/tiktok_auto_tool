# Phase 1: Data Model & Domain Entities

**Feature**: Multi-Image Video Slideshow with Smooth Transitions  
**Date**: 2026-11-04  
**Branch**: `005-multi-image-slideshow`  

## 1. Domain Model: `QueueItem` (Extended)

Managed by `services/queue_service.py`.

| Field | Type | Description | Default / Constraints |
|---|---|---|---|
| `id` | `int` | Sequential numeric identifier | Required, unique |
| `video_path` | `str` | Absolute filesystem path to source video | Required |
| `video_name` | `str` | Base filename of source video | Required |
| `duration_s` | `float` | Probed or estimated video duration in seconds | $\ge 0.0$ |
| `size_mb` | `float` | File size in megabytes | $\ge 0.0$ |
| `image_path` | `str` | Absolute path to primary image (used in single mode) | String |
| `image_name` | `str` | Base filename of primary image | String |
| `is_multi_image` | `bool` | Flag indicating whether multi-image mode is enabled | `False` |
| `image_count` | `int` | Desired number of images for slideshow | `10` (range: `2` to `50`) |
| `image_list` | `List[str]` | Ordered list of selected image filenames for slideshow | Defaults to 10 random images if enabled |
| `status` | `str` | `Chờ render` \| `Đang render` \| `Hoàn thành` \| `Lỗi` | String |
| `output_file` | `str` | Filename of rendered output video | String |
| `output_folder` | `str` | `outputs` \| `outputs-no-lyrics` | `outputs` |
| `has_lyrics` | `bool` | Whether rendered output contains lyrics overlay | `True` |
| `is_locked` | `bool` | Whether item is protected from accidental modifications | `False` |

---

## 2. Slideshow Compositor Spec

Used by `services/slideshow_service.py`.

| Field | Type | Description |
|---|---|---|
| `image_paths` | `List[str]` | List of resolved absolute paths for all slides in order |
| `total_duration` | `float` | Target video duration in seconds |
| `width` | `int` | Standard vertical width (`1080`) |
| `height` | `int` | Standard vertical height (`1920`) |
| `transition_type` | `str` | `'slide_left'` |
| `transition_dur` | `float` | Animation duration for each slide-in (e.g. `0.6s` to `0.8s`) |

#### Lifecycle / State Transitions:
1. **Single to Multi Toggle**: `is_multi_image = true`. If `image_list` is empty or has fewer than `image_count` items, sample `image_count` (10) random unique images from the configured image directory.
2. **Count Increment**: `image_count += 1`. Sample 1 new random image and append to `image_list`.
3. **Count Decrement**: `image_count -= 1`. Trim the last item from `image_list` (clamped to minimum 2).
4. **Re-roll Batch**: Resample `image_count` distinct random images and replace `image_list`.
5. **Slot Swap**: Replace `image_list[index]` with selected candidate image.
6. **Multi to Single Toggle**: `is_multi_image = false`. Revert rendering background to `image_path`.


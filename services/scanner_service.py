import os
import random
import subprocess
from typing import List, Tuple, Optional


class ScannerService:
    """
    Dedicated media discovery and file scanning service.
    Implements non-blocking lazy iterators, fast file-size duration heuristics,
    and fallback video duration extraction.
    """

    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.webm')

    @classmethod
    def scan_sample_images(cls, img_folder: str, limit: int = 60) -> List[str]:
        """
        Lazily collects up to `limit` valid image filenames using os.scandir.
        Does NOT traverse or collect all 25,000+ files, executing in <1ms.
        """
        if not img_folder or not os.path.isdir(img_folder):
            return []

        sample_images: List[str] = []
        try:
            with os.scandir(img_folder) as it:
                for entry in it:
                    if entry.is_file() and entry.name.lower().endswith(cls.IMAGE_EXTENSIONS):
                        sample_images.append(entry.name)
                        if len(sample_images) >= limit:
                            break
        except Exception:
            return []

        return sample_images

    @classmethod
    def scan_videos(cls, vid_folder: str) -> List[Tuple[str, str, int]]:
        """
        Fast enumeration of video files returning list of tuples:
        (filename, full_path, size_bytes).
        Sorted alphabetically by filename.
        """
        if not vid_folder or not os.path.isdir(vid_folder):
            return []

        videos: List[Tuple[str, str, int]] = []
        try:
            with os.scandir(vid_folder) as it:
                for entry in it:
                    if entry.is_file() and entry.name.lower().endswith(cls.VIDEO_EXTENSIONS):
                        try:
                            videos.append((entry.name, entry.path, entry.stat().st_size))
                        except Exception:
                            videos.append((entry.name, entry.path, 0))
        except Exception:
            return []

        videos.sort(key=lambda x: x[0])
        return videos

    @classmethod
    def get_random_image(cls, img_folder: str) -> Optional[str]:
        """
        Retrieves a single random image filename from the entire directory.
        Used specifically by modal 'Chọn ngẫu nhiên' action on-demand.
        """
        if not img_folder or not os.path.isdir(img_folder):
            return None

        try:
            images = [f for f in os.listdir(img_folder) if f.lower().endswith(cls.IMAGE_EXTENSIONS)]
            if images:
                return random.choice(images)
        except Exception:
            pass

        return None

    @classmethod
    def get_random_images_batch(cls, img_folder: str, count: int = 10, exclude: Optional[List[str]] = None) -> List[str]:
        """
        Samples up to `count` distinct random image filenames from the image directory.
        If folder has fewer images than count, returns all available images (shuffled).
        """
        if not img_folder or not os.path.isdir(img_folder):
            return []

        try:
            images = [f for f in os.listdir(img_folder) if f.lower().endswith(cls.IMAGE_EXTENSIONS)]
            if not images:
                return []
            
            exclude_set = set(exclude or [])
            pool = [x for x in images if x not in exclude_set]
            if len(pool) < count:
                pool = images  # Fall back to full pool if excluded set is too restrictive

            sample_size = min(count, len(pool))
            return random.sample(pool, sample_size)
        except Exception:
            return []

    @classmethod
    def estimate_fast_duration(cls, size_bytes: int) -> float:
        """
        Instantaneous duration heuristic based on video file size.
        Avoids blocking ffprobe processes during batch folder scanning.
        """
        size_mb = size_bytes / (1024 * 1024)
        return round(min(120.0, max(15.0, size_mb * 3.5)), 1)

    @classmethod
    def probe_single_video_duration(cls, video_path: str, default: float = 30.0) -> float:
        """
        Ultra-fast single video duration probe using ffprobe (<30ms).
        Falls back to MoviePy or default (30.0s) on error.
        """
        if not video_path or not os.path.exists(video_path):
            return default

        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                dur = float(res.stdout.strip())
                if dur > 0:
                    return round(dur, 2)
        except Exception:
            pass

        try:
            from moviepy import VideoFileClip
            with VideoFileClip(video_path) as clip:
                dur = clip.duration
                if dur and dur > 0:
                    return round(float(dur), 2)
        except Exception:
            pass

        return default


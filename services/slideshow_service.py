import os
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageEnhance
from moviepy import ImageClip, CompositeVideoClip


class SlideshowService:
    """
    Dedicated video slideshow generation service.
    Composites sequential images with smooth right-to-left horizontal slide transitions
    strictly adhering to standard 9:16 vertical formatting (1080x1920).
    """

    @classmethod
    def fit_image_vertical(cls, pil_img: Image.Image, target_w: int = 1080, target_h: int = 1920) -> Image.Image:
        """
        Fits an image into standard 9:16 vertical dimensions without distortion.
        Crops symmetrically and applies 20% brightness reduction for overlay contrast.
        """
        img_w, img_h = pil_img.size
        target_ratio = target_w / target_h
        img_ratio = img_w / img_h

        if img_ratio > target_ratio:
            new_h = target_h
            new_w = int(round(img_w * (target_h / img_h)))
        else:
            new_w = target_w
            new_h = int(round(img_h * (target_w / img_w)))

        resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - target_w) // 2)
        top = max(0, (new_h - target_h) // 2)
        cropped = resized.crop((left, top, left + target_w, top + target_h))

        # 20% background dimming for lyrics and logo contrast per Constitution Principle II
        enhancer = ImageEnhance.Brightness(cropped)
        return enhancer.enhance(0.8)

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
        Builds a CompositeVideoClip animating the given images sequentially
        with smooth right-to-left slide transitions matching total_duration.
        """
        valid_paths = [p for p in image_paths if p and os.path.exists(p)]
        if not valid_paths:
            raise ValueError("Không tìm thấy file ảnh hợp lệ nào để tạo slideshow!")

        num_images = len(valid_paths)
        total_duration = max(1.0, float(total_duration))

        # If only 1 image, return static ImageClip
        if num_images == 1:
            with Image.open(valid_paths[0]) as img:
                fitted = cls.fit_image_vertical(img.convert('RGB'), width, height)
                arr = np.array(fitted)
                return ImageClip(arr).with_duration(total_duration).with_position((0, 0))

        # Calculate time intervals
        interval = total_duration / num_images
        trans_dur = min(transition_duration, max(0.25, interval * 0.35))

        clips = []

        # Base layer: First slide (visible from start to finish)
        with Image.open(valid_paths[0]) as img0:
            fitted0 = cls.fit_image_vertical(img0.convert('RGB'), width, height)
            arr0 = np.array(fitted0)
            base_clip = ImageClip(arr0).with_start(0).with_duration(total_duration).with_position((0, 0))
            clips.append(base_clip)

        # Subsequent slides: Each enters from right to left over `trans_dur`
        for i in range(1, num_images):
            p = valid_paths[i]
            with Image.open(p) as img_i:
                fitted_i = cls.fit_image_vertical(img_i.convert('RGB'), width, height)
                arr_i = np.array(fitted_i)

            start_t = i * interval
            clip_dur = total_duration - start_t
            if clip_dur <= 0:
                continue

            def make_slide_pos(local_t, current_trans_dur=trans_dur, w=width):
                if local_t < current_trans_dur:
                    prog = max(0.0, min(1.0, float(local_t) / current_trans_dur))
                    # Quadratic ease-out for smooth natural deceleration
                    ease = 1.0 - (1.0 - prog) * (1.0 - prog)
                    x = int(round(w * (1.0 - ease)))
                    return (x, 0)
                return (0, 0)

            slide_clip = (
                ImageClip(arr_i)
                .with_start(start_t)
                .with_duration(clip_dur)
                .with_position(make_slide_pos)
            )
            clips.append(slide_clip)

        return CompositeVideoClip(clips, size=(width, height)).with_duration(total_duration)

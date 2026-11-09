import os
import subprocess
import time
from typing import Dict, Any, List, Optional


class FFmpegEncoderService:
    """
    High-Speed Native FFmpeg Media Encoding Engine.
    Detects and leverages hardware acceleration (NVENC, QSV, MediaFoundation)
    with seamless fallback to optimized software encoding (libx264 -preset ultrafast).
    Bypasses MoviePy's slow per-frame Python generator loops for static canvases.
    """

    _cached_encoder_info: Optional[Dict[str, Any]] = None

    @classmethod
    def probe_best_encoder(cls, force_reprobe: bool = False, profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Probes the host FFmpeg installation for the fastest available H.264 encoder.
        Respects the active performance profile ('max_speed' or 'balanced').
        Order of precedence:
        1. h264_nvenc (NVIDIA GPU hardware acceleration)
        2. h264_qsv   (Intel QuickSync Video hardware acceleration)
        3. h264_mf    (Windows MediaFoundation hardware acceleration)
        4. libx264    (High-performance CPU software encoder)
        """
        from services.config_service import ConfigService
        active_profile = (profile or ConfigService.get_performance_profile() or 'max_speed').lower()

        if cls._cached_encoder_info and not force_reprobe:
            if cls._cached_encoder_info.get('profile') == active_profile:
                return cls._cached_encoder_info

        if active_profile == 'balanced':
            nvenc_preset = ['-preset', 'p5']
            qsv_preset = ['-preset', 'medium']
            x264_preset = ['-preset', 'fast']
        else:
            nvenc_preset = ['-preset', 'p4', '-tune', 'll']
            qsv_preset = ['-preset', 'veryfast']
            x264_preset = ['-preset', 'ultrafast', '-tune', 'fastdecode']

        candidates = [
            {
                'encoder': 'h264_nvenc',
                'name': f"NVIDIA NVENC Hardware ({'Tối đa tốc độ' if active_profile == 'max_speed' else 'Cân bằng'})",
                'is_hardware': True,
                'preset_args': nvenc_preset,
                'test_cmd': ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'nullsrc=s=64x64:d=0.05', '-c:v', 'h264_nvenc', '-f', 'null', '-']
            },
            {
                'encoder': 'h264_qsv',
                'name': f"Intel QuickSync Hardware ({'Tối đa tốc độ' if active_profile == 'max_speed' else 'Cân bằng'})",
                'is_hardware': True,
                'preset_args': qsv_preset,
                'test_cmd': ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'nullsrc=s=64x64:d=0.05', '-c:v', 'h264_qsv', '-f', 'null', '-']
            },
            {
                'encoder': 'h264_mf',
                'name': 'Windows MediaFoundation Hardware',
                'is_hardware': True,
                'preset_args': ['-rate_control', 'cbr'],
                'test_cmd': ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'nullsrc=s=64x64:d=0.05', '-c:v', 'h264_mf', '-f', 'null', '-']
            },
            {
                'encoder': 'libx264',
                'name': f"CPU libx264 ({'ultrafast' if active_profile == 'max_speed' else 'fast'})",
                'is_hardware': False,
                'preset_args': x264_preset,
                'test_cmd': ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'nullsrc=s=64x64:d=0.05', '-c:v', 'libx264', '-preset', 'ultrafast', '-f', 'null', '-']
            }
        ]

        selected = None
        for cand in candidates:
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                res = subprocess.run(
                    cand['test_cmd'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    creationflags=creationflags
                )
                if res.returncode == 0:
                    selected = {
                        'encoder': cand['encoder'],
                        'name': cand['name'],
                        'is_hardware': cand['is_hardware'],
                        'preset_args': cand['preset_args'],
                        'profile': active_profile
                    }
                    print(f"🚀 [FFmpegEncoder] Đã kích hoạt bộ mã hóa: {cand['name']} ({cand['encoder']})")
                    break
            except Exception as e:
                continue

        if not selected:
            # Default fallback
            selected = {
                'encoder': 'libx264',
                'name': 'CPU libx264 (default)',
                'is_hardware': False,
                'preset_args': x264_preset,
                'profile': active_profile
            }

        cls._cached_encoder_info = selected
        return selected

    @classmethod
    def render_static_video(
        cls,
        canvas_path: str,
        audio_path: str,
        output_path: str,
        duration: float,
        fps: int = 24,
        encoder_override: Optional[str] = None
    ) -> bool:
        """
        Directly renders a vertical MP4 from a pre-composed 1080x1920 canvas image and an audio file
        via native FFmpeg stream looping. Eliminates Python frame evaluation overhead entirely.
        """
        if not os.path.exists(canvas_path):
            raise FileNotFoundError(f"Không tìm thấy file canvas: {canvas_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Không tìm thấy file âm thanh: {audio_path}")

        duration = max(0.5, float(duration))
        info = cls.probe_best_encoder()
        encoder = encoder_override or info['encoder']
        preset_args = info['preset_args'] if not encoder_override else ['-preset', 'ultrafast']

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-framerate', str(fps),
            '-i', canvas_path,
            '-i', audio_path,
            '-t', f"{duration:.3f}",
            '-c:v', encoder,
            *preset_args,
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            output_path
        ]

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        t_start = time.time()
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
            creationflags=creationflags
        )

        if res.returncode != 0:
            err_msg = res.stderr.decode('utf-8', errors='ignore')
            print(f"⚠️ [FFmpegEncoder] Bộ mã hóa {encoder} gặp sự cố: {err_msg[:300]}")
            # Fallback to libx264 ultrafast if hardware encoder failed
            if encoder != 'libx264':
                print("🔄 [FFmpegEncoder] Tự động chuyển đổi sang phần mềm libx264 (ultrafast)...")
                fallback_cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1',
                    '-framerate', str(fps),
                    '-i', canvas_path,
                    '-i', audio_path,
                    '-t', f"{duration:.3f}",
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-tune', 'fastdecode',
                    '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-shortest',
                    output_path
                ]
                fb_res = subprocess.run(
                    fallback_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=180,
                    creationflags=creationflags
                )
                if fb_res.returncode != 0:
                    fb_err = fb_res.stderr.decode('utf-8', errors='ignore')
                    raise RuntimeError(f"FFmpeg fallback thất bại: {fb_err[:400]}")
            else:
                raise RuntimeError(f"FFmpeg encode thất bại: {err_msg[:400]}")

        elapsed = time.time() - t_start
        print(f"⚡ [FFmpegEncoder] Mã hóa video tĩnh hoàn tất trong {elapsed:.2f}s ({duration/elapsed:.1f}x thời gian thực)")
        return True

    @classmethod
    def render_slideshow_video(
        cls,
        slide_canvas_paths: List[str],
        audio_path: str,
        output_path: str,
        total_duration: float,
        transition_duration: float = 0.65,
        fps: int = 24
    ) -> bool:
        """
        Encodes sequential 1080x1920 slide images with native FFmpeg filtergraph (xfade slideleft)
        or high-throughput pipeline matching total_duration.
        """
        valid_slides = [p for p in slide_canvas_paths if p and os.path.exists(p)]
        if not valid_slides:
            raise ValueError("Không có ảnh slideshow hợp lệ để mã hóa!")

        if len(valid_slides) == 1:
            return cls.render_static_video(valid_slides[0], audio_path, output_path, total_duration, fps)

        num_slides = len(valid_slides)
        total_duration = max(1.0, float(total_duration))
        interval = total_duration / num_slides
        trans_dur = min(transition_duration, max(0.25, interval * 0.35))

        info = cls.probe_best_encoder()
        encoder = info['encoder']
        preset_args = info['preset_args']

        # Construct FFmpeg xfade filtergraph
        # Each input loops for (interval + trans_dur)
        cmd = ['ffmpeg', '-y']
        for p in valid_slides:
            cmd.extend(['-loop', '1', '-t', f"{(interval + trans_dur):.3f}", '-i', p])
        cmd.extend(['-i', audio_path])

        filter_parts = []
        last_out = "0:v"
        for i in range(1, num_slides):
            curr_in = f"{i}:v"
            next_out = f"v{i}"
            offset = i * interval
            filter_parts.append(f"[{last_out}][{curr_in}]xfade=transition=slideleft:duration={trans_dur:.3f}:offset={offset:.3f}[{next_out}]")
            last_out = next_out

        filter_graph = ";".join(filter_parts)
        audio_idx = num_slides

        cmd.extend([
            '-filter_complex', filter_graph,
            '-map', f"[{last_out}]",
            '-map', f"{audio_idx}:a",
            '-t', f"{total_duration:.3f}",
            '-c:v', encoder,
            *preset_args,
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            output_path
        ])

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        t_start = time.time()
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=240,
            creationflags=creationflags
        )

        if res.returncode != 0:
            # Fallback to software encoding with filtergraph
            cmd_fb = ['ffmpeg', '-y']
            for p in valid_slides:
                cmd_fb.extend(['-loop', '1', '-t', f"{(interval + trans_dur):.3f}", '-i', p])
            cmd_fb.extend(['-i', audio_path])
            cmd_fb.extend([
                '-filter_complex', filter_graph,
                '-map', f"[{last_out}]",
                '-map', f"{audio_idx}:a",
                '-t', f"{total_duration:.3f}",
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'fastdecode',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                output_path
            ])
            fb_res = subprocess.run(
                cmd_fb,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=240,
                creationflags=creationflags
            )
            if fb_res.returncode != 0:
                err_msg = fb_res.stderr.decode('utf-8', errors='ignore')
                raise RuntimeError(f"FFmpeg slideshow encode thất bại: {err_msg[:400]}")

        elapsed = time.time() - t_start
        print(f"⚡ [FFmpegEncoder] Mã hóa slideshow {num_slides} ảnh hoàn tất trong {elapsed:.2f}s ({total_duration/elapsed:.1f}x)")
        return True


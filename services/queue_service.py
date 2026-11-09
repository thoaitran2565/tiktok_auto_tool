import os
import random
import threading
from typing import Dict, List, Any, Optional, Tuple

from services.config_service import ConfigService
from services.scanner_service import ScannerService
from services.progress_manager import progress_manager
from services.telemetry_manager import telemetry_manager


class QueueService:
    """
    Dedicated thread-safe domain service managing the render queue state,
    folder binding, non-destructive synchronization, and item modifications.
    """

    _lock = threading.Lock()
    _session_data: Dict[str, Any] = {
        'image_folder': '',
        'video_folder': '',
        'queue': []
    }

    @classmethod
    def set_session_folders(cls, img_folder: str, vid_folder: str) -> None:
        with cls._lock:
            cls._session_data['image_folder'] = img_folder.strip()
            cls._session_data['video_folder'] = vid_folder.strip()

    @classmethod
    def get_session_folders(cls) -> Tuple[str, str]:
        with cls._lock:
            return (
                cls._session_data.get('image_folder', ''),
                cls._session_data.get('video_folder', '')
            )

    @classmethod
    def get_queue(cls) -> List[Dict[str, Any]]:
        with cls._lock:
            return list(cls._session_data.get('queue', []))

    @classmethod
    def get_item(cls, item_id: int) -> Optional[Dict[str, Any]]:
        with cls._lock:
            for item in cls._session_data.get('queue', []):
                if item.get('id') == item_id:
                    return item
        return None

    get_item_by_id = get_item

    @classmethod
    def init_queue_from_folders(cls, img_folder: str, vid_folder: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validates directories, gathers lazy sample images and video files,
        and initializes the render queue with instantaneous heuristics.
        """
        img_folder = img_folder.strip()
        vid_folder = vid_folder.strip()

        if not img_folder or not vid_folder or not os.path.isdir(img_folder) or not os.path.isdir(vid_folder):
            return False, 'Đường dẫn thư mục không hợp lệ hoặc không tồn tại!', {}

        # Persist to config.json
        ConfigService.save_config(img_folder, vid_folder)

        # Lazy image scanning (<1ms)
        sample_images = ScannerService.scan_sample_images(img_folder, limit=60)
        if not sample_images:
            return False, 'Thư mục ảnh không chứa file ảnh hợp lệ nào!', {}

        # Fast video enumeration (<5ms)
        videos = ScannerService.scan_videos(vid_folder)
        if not videos:
            return False, 'Thư mục video không chứa file video nào!', {}

        queue = []
        for idx, (v_name, v_path, v_size) in enumerate(videos):
            rand_image = random.choice(sample_images)
            size_mb = round(v_size / (1024 * 1024), 2)
            fast_dur_s = ScannerService.estimate_fast_duration(v_size)
            queue.append({
                'id': idx,
                'video_path': v_path,
                'video_name': v_name,
                'duration_s': fast_dur_s,
                'size_mb': size_mb,
                'image_path': os.path.join(img_folder, rand_image),
                'image_name': rand_image,
                'status': 'Chờ render',
                'output_file': '',
                'output_folder': 'outputs',
                'has_lyrics': True,
                'is_locked': False,
                'is_multi_image': False,
                'image_count': 10,
                'image_list': []
            })

        with cls._lock:
            cls._session_data['image_folder'] = img_folder
            cls._session_data['video_folder'] = vid_folder
            cls._session_data['queue'] = queue

        serialized = cls.serialize_queue_for_client(queue)
        return True, None, {
            'image_folder': img_folder,
            'video_folder': vid_folder,
            'available_images': sample_images,
            'queue': serialized
        }

    @classmethod
    def refresh_queue_state(cls) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Non-destructively synchronizes queue with active directory contents.
        Preserves in-progress, completed, and locked items, appends new videos,
        and returns active render item id without disrupting jobs.
        """
        img_folder, vid_folder = cls.get_session_folders()

        if not img_folder or not vid_folder or not os.path.isdir(img_folder) or not os.path.isdir(vid_folder):
            return False, 'Thư mục chưa được thiết lập hoặc không còn tồn tại!', {}

        sample_images = ScannerService.scan_sample_images(img_folder, limit=60)
        current_videos = ScannerService.scan_videos(vid_folder)

        with cls._lock:
            existing_queue = cls._session_data.get('queue', [])
            existing_paths = {item['video_path']: item for item in existing_queue}

            new_items_added = 0
            max_id = max([item['id'] for item in existing_queue], default=-1)

            for v_name, v_path, v_size in current_videos:
                if v_path not in existing_paths:
                    max_id += 1
                    rand_image = random.choice(sample_images) if sample_images else ''
                    size_mb = round(v_size / (1024 * 1024), 2)
                    fast_dur_s = ScannerService.estimate_fast_duration(v_size)
                    new_item = {
                        'id': max_id,
                        'video_path': v_path,
                        'video_name': v_name,
                        'duration_s': fast_dur_s,
                        'size_mb': size_mb,
                        'image_path': os.path.join(img_folder, rand_image) if rand_image else '',
                        'image_name': rand_image,
                        'status': 'Chờ render',
                        'output_file': '',
                        'output_folder': 'outputs',
                        'has_lyrics': True,
                        'is_locked': False,
                        'is_multi_image': False,
                        'image_count': 10,
                        'image_list': []
                    }
                    existing_queue.append(new_item)
                    new_items_added += 1

            cls._session_data['queue'] = existing_queue
            snapshot = list(existing_queue)

        # Detect active rendering item
        all_prog = progress_manager.get_all_progress()
        active_item_id = None
        for k, v in all_prog.items():
            if v.get('status') == 'processing':
                active_item_id = v.get('item_id')
                break

        return True, None, {
            'image_folder': img_folder,
            'video_folder': vid_folder,
            'queue': cls.serialize_queue_for_client(snapshot),
            'available_images': sample_images,
            'new_items_added': new_items_added,
            'active_item_id': active_item_id
        }

    @classmethod
    def update_item_image(
        cls,
        item_id: int,
        image_name: Optional[str] = None,
        is_multi_image: Optional[bool] = None,
        image_count: Optional[int] = None,
        image_list: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Updates image configuration (single image or multi-image) for a queue item.
        """
        img_folder, _ = cls.get_session_folders()
        if not img_folder:
            return False, 'Chưa cấu hình thư mục ảnh!'

        with cls._lock:
            for item in cls._session_data.get('queue', []):
                if item.get('id') == item_id:
                    if image_name is not None and image_name.strip():
                        new_image_path = os.path.join(img_folder, image_name)
                        if os.path.exists(new_image_path):
                            item['image_path'] = new_image_path
                            item['image_name'] = image_name

                    if is_multi_image is not None:
                        item['is_multi_image'] = bool(is_multi_image)
                        if item['is_multi_image'] and not item.get('image_list'):
                            cnt = item.get('image_count', 10)
                            sampled = ScannerService.get_random_images_batch(img_folder, count=cnt)
                            item['image_list'] = sampled
                            if sampled:
                                item['image_name'] = sampled[0]
                                item['image_path'] = os.path.join(img_folder, sampled[0])

                    if image_count is not None:
                        item['image_count'] = max(2, min(50, int(image_count)))

                    if image_list is not None and isinstance(image_list, list):
                        valid_list = [x for x in image_list if os.path.exists(os.path.join(img_folder, x))]
                        item['image_list'] = valid_list
                        item['image_count'] = len(valid_list)
                        if valid_list:
                            item['image_name'] = valid_list[0]
                            item['image_path'] = os.path.join(img_folder, valid_list[0])

                    from services.render_pipeline import render_pipeline
                    render_pipeline.clear_prefetch(item_id)
                    return True, None

        return False, 'Không tìm thấy video trong hàng đợi!'

    @classmethod
    def toggle_multi_image(cls, item_id: int, enabled: bool) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Toggles multi-image mode for an item. If enabling and image_list is empty,
        samples 10 random images automatically.
        """
        img_folder, _ = cls.get_session_folders()
        if not img_folder:
            return False, 'Chưa cấu hình thư mục ảnh!', {}

        with cls._lock:
            for item in cls._session_data.get('queue', []):
                if item.get('id') == item_id:
                    item['is_multi_image'] = bool(enabled)
                    if item['is_multi_image']:
                        cnt = item.get('image_count', 10)
                        curr_list = item.get('image_list', [])
                        if not curr_list or len(curr_list) < cnt:
                            sampled = ScannerService.get_random_images_batch(img_folder, count=cnt)
                            item['image_list'] = sampled
                            if sampled:
                                item['image_name'] = sampled[0]
                                item['image_path'] = os.path.join(img_folder, sampled[0])
                    item_dict = {
                        'id': item_id,
                        'is_multi_image': item['is_multi_image'],
                        'image_count': item.get('image_count', 10),
                        'image_list': item.get('image_list', [])
                    }
                    from services.render_pipeline import render_pipeline
                    render_pipeline.clear_prefetch(item_id)
                    return True, None, {
                        'item': item_dict,
                        'is_multi_image': item['is_multi_image'],
                        'image_count': item.get('image_count', 10),
                        'image_list': item.get('image_list', [])
                    }

        return False, 'Không tìm thấy video trong hàng đợi!', {}

    @classmethod
    def update_multi_image_count(cls, item_id: int, count: int) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Updates the image count for an item, sampling new random images if increasing,
        or trimming list if decreasing.
        """
        img_folder, _ = cls.get_session_folders()
        if not img_folder:
            return False, 'Chưa cấu hình thư mục ảnh!', {}

        target_count = max(2, min(50, int(count)))

        with cls._lock:
            for item in cls._session_data.get('queue', []):
                if item.get('id') == item_id:
                    item['image_count'] = target_count
                    curr_list = list(item.get('image_list', []))

                    if len(curr_list) < target_count:
                        diff = target_count - len(curr_list)
                        more = ScannerService.get_random_images_batch(img_folder, count=diff, exclude=curr_list)
                        curr_list.extend(more)
                    elif len(curr_list) > target_count:
                        curr_list = curr_list[:target_count]

                    item['image_list'] = curr_list
                    if curr_list:
                        item['image_name'] = curr_list[0]
                        item['image_path'] = os.path.join(img_folder, curr_list[0])

                    item_dict = {
                        'id': item_id,
                        'is_multi_image': item.get('is_multi_image', False),
                        'image_count': target_count,
                        'image_list': curr_list
                    }
                    from services.render_pipeline import render_pipeline
                    render_pipeline.clear_prefetch(item_id)
                    return True, None, {
                        'item': item_dict,
                        'image_count': target_count,
                        'image_list': curr_list
                    }

        return False, 'Không tìm thấy video trong hàng đợi!', {}

    @classmethod
    def set_multi_image_list(cls, item_id: int, image_list: List[str]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Updates the complete ordered image list for a multi-image item.
        """
        img_folder, _ = cls.get_session_folders()
        if not img_folder:
            return False, 'Chưa cấu hình thư mục ảnh!', {}

        valid_list = [x for x in image_list if os.path.exists(os.path.join(img_folder, x))]
        if len(valid_list) < 2:
            return False, 'Danh sách nhiều ảnh cần tối thiểu 2 ảnh hợp lệ!', {}

        with cls._lock:
            for item in cls._session_data.get('queue', []):
                if item.get('id') == item_id:
                    item['is_multi_image'] = True
                    item['image_list'] = valid_list
                    item['image_count'] = len(valid_list)
                    item['image_name'] = valid_list[0]
                    item['image_path'] = os.path.join(img_folder, valid_list[0])
                    item_dict = {
                        'id': item_id,
                        'is_multi_image': True,
                        'image_count': len(valid_list),
                        'image_list': valid_list
                    }
                    from services.render_pipeline import render_pipeline
                    render_pipeline.clear_prefetch(item_id)
                    return True, None, {
                        'item': item_dict,
                        'is_multi_image': True,
                        'image_count': len(valid_list),
                        'image_list': valid_list
                    }

        return False, 'Không tìm thấy video trong hàng đợi!', {}

    @classmethod
    def reroll_multi_images(cls, item_id: int) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Resamples a brand-new random batch of images for the specified item.
        """
        img_folder, _ = cls.get_session_folders()
        if not img_folder:
            return False, 'Chưa cấu hình thư mục ảnh!', {}

        with cls._lock:
            for item in cls._session_data.get('queue', []):
                if item.get('id') == item_id:
                    cnt = item.get('image_count', 10)
                    fresh = ScannerService.get_random_images_batch(img_folder, count=cnt)
                    if not fresh:
                        return False, 'Không đủ ảnh trong thư mục để bốc ngẫu nhiên!', {}
                    item['image_list'] = fresh
                    item['image_name'] = fresh[0]
                    item['image_path'] = os.path.join(img_folder, fresh[0])
                    item_dict = {
                        'id': item_id,
                        'is_multi_image': True,
                        'image_count': len(fresh),
                        'image_list': fresh
                    }
                    from services.render_pipeline import render_pipeline
                    render_pipeline.clear_prefetch(item_id)
                    return True, None, {
                        'item': item_dict,
                        'is_multi_image': True,
                        'image_count': len(fresh),
                        'image_list': fresh
                    }

        return False, 'Không tìm thấy video trong hàng đợi!', {}

    @classmethod
    def get_progress_summary(cls, item_id: Optional[int] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Computes queue statistics (total, completed, pending, failed, active_item_id,
        and estimated remaining time) and returns (summary, progress_payload).
        """
        queue = cls.get_queue()
        total_items = len(queue)
        completed_items = sum(1 for x in queue if x.get('status') == 'Hoàn thành')
        failed_items = sum(1 for x in queue if x.get('status') == 'Lỗi')
        pending_items = max(0, total_items - completed_items - failed_items)

        all_prog = progress_manager.get_all_progress()
        active_item_id = None
        active_remaining = 0.0
        for k, v in all_prog.items():
            if v.get('status') == 'processing':
                active_item_id = v.get('item_id')
                active_remaining = v.get('estimated_remaining_s', 0.0)
                break

        unstarted_est = sum(
            telemetry_manager.predict_duration(x.get('duration_s', 30.0), x.get('size_mb', 0.0))
            for x in queue
            if x.get('status') not in ('Hoàn thành', 'Lỗi') and x.get('id') != active_item_id
        )
        est_pending_queue = active_remaining + unstarted_est

        summary = {
            'total_items': total_items,
            'completed_items': completed_items,
            'pending_items': pending_items,
            'failed_items': failed_items,
            'active_item_id': active_item_id,
            'estimated_queue_remaining_s': int(round(est_pending_queue)),
            'prefetch_map': cls.get_prefetch_map()
        }

        if item_id is not None:
            prog = progress_manager.get_item_progress(item_id)
            progress_payload = {str(item_id): prog} if prog else {}
        else:
            progress_payload = all_prog

        return summary, progress_payload

    @classmethod
    def get_render_predictions(cls) -> Dict[str, Any]:
        """
        Derives upfront duration estimates for all items currently in the queue.
        """
        queue = cls.get_queue()
        predictions = []
        total_est = 0.0
        profile = telemetry_manager.get_model_profile()

        for item in queue:
            vid_path = item.get('video_path', '')
            size_mb = item.get('size_mb', 0.0)
            dur_s = item.get('duration_s')
            if dur_s is None or dur_s <= 0:
                dur_s = ScannerService.probe_single_video_duration(vid_path)
                item['duration_s'] = dur_s
            if not size_mb and os.path.exists(vid_path):
                try:
                    size_mb = round(os.path.getsize(vid_path) / (1024 * 1024), 2)
                    item['size_mb'] = size_mb
                except Exception:
                    pass

            est_s = telemetry_manager.predict_duration(dur_s, size_mb)
            item['estimated_total_s'] = est_s
            predictions.append({
                'id': item.get('id'),
                'video_name': item.get('video_name'),
                'duration_s': dur_s,
                'size_mb': size_mb,
                'estimated_total_s': est_s,
                'is_locked': item.get('is_locked', item.get('status') == 'Hoàn thành'),
                'confidence': 'low' if profile.get('is_cold_start') else 'high'
            })
            if item.get('status') != 'Hoàn thành':
                total_est += est_s

        return {
            'success': True,
            'is_cold_start': profile.get('is_cold_start', True),
            'telemetry_count': profile.get('sample_count', 0),
            'predictions': predictions,
            'total_queue_estimate_s': int(round(total_est))
        }

    @classmethod
    def serialize_queue_for_client(cls, queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Serializes internal queue representations into JSON-ready dictionaries
        adhering to frontend requirements.
        """
        prefetch_map = cls.get_prefetch_map()
        return [{
            'id': item['id'],
            'video_name': item['video_name'],
            'duration_s': item.get('duration_s', 30.0),
            'size_mb': item.get('size_mb', 0.0),
            'image_name': item.get('image_name', ''),
            'status': item.get('status', 'Chờ render'),
            'output_file': item.get('output_file', ''),
            'output_folder': item.get('output_folder', 'outputs'),
            'has_lyrics': item.get('has_lyrics', True),
            'is_locked': item.get('is_locked', item.get('status') == 'Hoàn thành'),
            'is_multi_image': item.get('is_multi_image', False),
            'image_count': item.get('image_count', 10),
            'image_list': item.get('image_list', []),
            'prefetch_status': prefetch_map.get(item['id'], 'idle')
        } for item in queue]

    @classmethod
    def get_next_pending_item(cls, current_item_id: int) -> Optional[Dict[str, Any]]:
        """
        Identifies the next eligible item in the queue for asynchronous pre-fetching.
        """
        with cls._lock:
            queue = cls._session_data.get('queue', [])
            current_index = -1
            for idx, item in enumerate(queue):
                if item.get('id') == current_item_id:
                    current_index = idx
                    break

            if current_index >= 0:
                for item in queue[current_index + 1:]:
                    if item.get('status') == 'Chờ render' and not item.get('is_locked', False):
                        return dict(item)

            for item in queue:
                if item.get('id') != current_item_id and item.get('status') == 'Chờ render' and not item.get('is_locked', False):
                    return dict(item)

        return None

    @classmethod
    def start_prefetch_for_next(cls, current_item_id: int) -> Optional[Dict[str, Any]]:
        """
        Finds the upcoming queue item and dispatches pre_fetch_item() in a background daemon thread.
        """
        from services.render_pipeline import render_pipeline

        next_item = cls.get_next_pending_item(current_item_id)
        if not next_item:
            return None

        img_folder, _ = cls.get_session_folders()
        if not img_folder:
            img_folder, _ = ConfigService.get_configured_folders()

        is_multi = bool(next_item.get('is_multi_image'))
        img_list = next_item.get('image_list', [])
        multi_paths = []
        if is_multi and img_list and img_folder:
            multi_paths = [os.path.join(img_folder, img) for img in img_list if os.path.exists(os.path.join(img_folder, img))]

        render_pipeline.start_prefetch_thread(
            item_id=next_item['id'],
            video_path=next_item.get('video_path', ''),
            image_path=next_item.get('image_path', ''),
            is_multi_image=(is_multi and len(multi_paths) >= 2),
            image_paths=multi_paths
        )
        return next_item

    @classmethod
    def get_prefetch_map(cls) -> Dict[int, str]:
        """
        Returns a mapping of item_id -> prefetch status ('in_progress', 'ready', 'failed').
        """
        from services.render_pipeline import render_pipeline
        with render_pipeline._prefetch_lock:
            return {
                k: v.get('status', 'idle')
                for k, v in render_pipeline._prefetch_cache.items()
            }


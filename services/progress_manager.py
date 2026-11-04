import time
import threading
from typing import Dict, Any, Optional, List

# Centralized stage definition: ID, Vietnamese display label, order, estimated percentage weight
DEFAULT_STAGES = [
    {"id": "audio_extraction", "label": "Trích xuất âm thanh", "order": 1, "weight": 10},
    {"id": "speech_transcription", "label": "Nhận diện giọng nói (Whisper)", "order": 2, "weight": 30},
    {"id": "lyric_refinement", "label": "Làm sạch lời bài hát AI", "order": 3, "weight": 20},
    {"id": "visual_generation", "label": "Tạo hình ảnh & lyrics trong suốt", "order": 4, "weight": 10},
    {"id": "media_encoding", "label": "Ghép video & mã hóa MP4", "order": 5, "weight": 25},
    {"id": "finalization", "label": "Xác thực & dọn dẹp", "order": 6, "weight": 5},
]

STAGE_CEILINGS = {
    "audio_extraction": 10,
    "speech_transcription": 40,
    "lyric_refinement": 60,
    "visual_generation": 70,
    "media_encoding": 95,
    "finalization": 100
}

class ProgressManager:
    """
    Thread-safe in-memory store for active rendering progress states.
    Manages live stage transitions, elapsed durations, and dynamic completion percentages.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._items: Dict[str, Dict[str, Any]] = {}

    def init_item(self, item_id: Any, video_name: str, estimated_total_s: float = 0.0) -> Dict[str, Any]:
        """Initialize or reset an item in the progress tracker."""
        with self._lock:
            key = str(item_id)
            stages = []
            for s in DEFAULT_STAGES:
                stages.append({
                    "id": s["id"],
                    "label": s["label"],
                    "order": s["order"],
                    "status": "pending",
                    "started_at": None,
                    "finished_at": None,
                    "duration_s": 0.0,
                    "error_message": None
                })

            item_state = {
                "item_id": item_id,
                "video_name": video_name,
                "status": "processing",
                "current_stage_id": DEFAULT_STAGES[0]["id"],
                "current_stage_label": DEFAULT_STAGES[0]["label"],
                "percent": 0,
                "started_at": time.time(),
                "elapsed_s": 0.0,
                "estimated_total_s": max(0.0, float(estimated_total_s)),
                "estimated_remaining_s": max(0.0, float(estimated_total_s)),
                "stages": stages,
                "error": None,
                "output_file": None
            }
            self._items[key] = item_state
            return dict(item_state)

    def update_stage(self, item_id: Any, stage_id: str, status: str = "active", error_message: Optional[str] = None):
        """Update an item's active stage status ('active', 'completed', 'failed')."""
        with self._lock:
            key = str(item_id)
            if key not in self._items:
                return

            item = self._items[key]
            now = time.time()
            item["elapsed_s"] = int(round(now - item.get("started_at", now)))

            # Recalculate remaining time in integer seconds
            est_total = item.get("estimated_total_s", 0.0)
            if est_total > 0:
                item["estimated_remaining_s"] = max(0, int(round(est_total - item["elapsed_s"])))

            found = False
            completed_weight = 0
            for stage in item["stages"]:
                # Accumulate weight for completed stages
                if stage["status"] == "completed":
                    stage_def = next((s for s in DEFAULT_STAGES if s["id"] == stage["id"]), None)
                    if stage_def:
                        completed_weight += stage_def["weight"]

                if stage["id"] == stage_id:
                    found = True
                    stage["status"] = status
                    if status == "active":
                        stage["started_at"] = now
                        item["current_stage_id"] = stage_id
                        item["current_stage_label"] = stage["label"]
                        # Ceiling plateau: active stage interpolates but cannot exceed ceiling
                        stage_def = next((s for s in DEFAULT_STAGES if s["id"] == stage_id), None)
                        if stage_def:
                            completed_weight += int(stage_def["weight"] * 0.5)
                    elif status == "completed":
                        stage["finished_at"] = now
                        if stage.get("started_at"):
                            stage["duration_s"] = int(round(now - stage["started_at"]))
                        stage_def = next((s for s in DEFAULT_STAGES if s["id"] == stage_id), None)
                        if stage_def:
                            completed_weight += stage_def["weight"]
                    elif status == "failed":
                        stage["finished_at"] = now
                        stage["error_message"] = error_message
                        item["status"] = "error"
                        item["error"] = error_message

            # Cap active percentage strictly at stage ceiling before finalization
            ceiling = STAGE_CEILINGS.get(stage_id, 95)
            if status == "active":
                item["percent"] = min(ceiling - 1, completed_weight)
            elif status == "completed":
                item["percent"] = min(ceiling, completed_weight)
            else:
                item["percent"] = min(95, completed_weight)

    def complete_item(self, item_id: Any, output_file: Optional[str] = None):
        """Mark entire item rendering as completed."""
        with self._lock:
            key = str(item_id)
            if key not in self._items:
                return

            item = self._items[key]
            now = time.time()
            item["elapsed_s"] = int(round(now - item.get("started_at", now)))
            item["estimated_remaining_s"] = 0
            item["percent"] = 100
            item["status"] = "completed"
            item["output_file"] = output_file
            item["current_stage_id"] = "completed"
            item["current_stage_label"] = "Hoàn thành"

            for stage in item["stages"]:
                if stage["status"] != "completed":
                    stage["status"] = "completed"
                    if not stage.get("finished_at"):
                        stage["finished_at"] = now

    def fail_item(self, item_id: Any, stage_id: Optional[str] = None, error_message: str = "Unknown error"):
        """Mark item rendering as failed, pinpointing the specific failing stage."""
        with self._lock:
            key = str(item_id)
            if key not in self._items:
                return

            item = self._items[key]
            now = time.time()
            item["elapsed_s"] = int(round(now - item.get("started_at", now)))
            item["status"] = "error"
            item["error"] = error_message
            target_stage = stage_id or item.get("current_stage_id")

            for stage in item["stages"]:
                if stage["id"] == target_stage:
                    stage["status"] = "failed"
                    stage["error_message"] = error_message
                    stage["finished_at"] = now
                    break

    def get_item_progress(self, item_id: Any) -> Optional[Dict[str, Any]]:
        """Return a snapshot of progress state for a specific item."""
        with self._lock:
            key = str(item_id)
            item = self._items.get(key)
            if not item:
                return None
            res = dict(item)
            if res["status"] == "processing":
                res["elapsed_s"] = round(time.time() - res.get("started_at", time.time()), 1)
                est_total = res.get("estimated_total_s", 0.0)
                if est_total > 0:
                    res["estimated_remaining_s"] = max(1.0, round(est_total - res["elapsed_s"], 1))
            res["stages"] = [dict(s) for s in item["stages"]]
            return res

    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """Return snapshots of all tracked items."""
        with self._lock:
            result = {}
            now = time.time()
            for key, item in self._items.items():
                copy_item = dict(item)
                if copy_item["status"] == "processing":
                    copy_item["elapsed_s"] = round(now - copy_item.get("started_at", now), 1)
                    est_total = copy_item.get("estimated_total_s", 0.0)
                    if est_total > 0:
                        copy_item["estimated_remaining_s"] = max(1.0, round(est_total - copy_item["elapsed_s"], 1))
                copy_item["stages"] = [dict(s) for s in item["stages"]]
                result[key] = copy_item
            return result

    def clear(self):
        """Clear all in-memory items."""
        with self._lock:
            self._items.clear()


# Global shared instance
progress_manager = ProgressManager()


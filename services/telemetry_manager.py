import os
import json
import time
from datetime import datetime
import threading
from typing import Dict, Any, List, Optional

TELEMETRY_FILE = os.path.join("data", "render_telemetry.json")
MAX_TELEMETRY_RECORDS = 100

class TelemetryManager:
    """
    Manages persistence of historical render performance telemetry
    and calculates statistical profiles for predictive duration estimation.
    """
    def __init__(self, filepath: str = TELEMETRY_FILE):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self):
        """Ensure parent directory and JSON file exist."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ Error creating telemetry file: {e}")

    def load_records(self) -> List[Dict[str, Any]]:
        """Load all telemetry records from disk."""
        with self._lock:
            if not os.path.exists(self.filepath):
                return []
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception as e:
                print(f"⚠️ Error reading telemetry records: {e}")
                return []

    def record_render(
        self,
        video_name: str,
        input_duration_s: float,
        input_size_mb: float,
        stage_durations: Dict[str, float],
        api_latency_ms: float,
        total_duration_s: float,
        status: str = "completed"
    ) -> Dict[str, Any]:
        """
        Record performance metrics of a completed or failed render.
        Enforces a rolling window of max 100 records (pruning oldest).
        """
        record = {
            "id": f"tel_{int(time.time() * 1000)}",
            "timestamp": datetime.now().isoformat(),
            "video_name": video_name,
            "input_duration_s": round(max(0.1, float(input_duration_s)), 2),
            "input_size_mb": round(max(0.0, float(input_size_mb)), 2),
            "stage_durations": {k: round(float(v), 2) for k, v in stage_durations.items()},
            "api_latency_ms": round(max(0.0, float(api_latency_ms)), 1),
            "total_duration_s": round(max(0.1, float(total_duration_s)), 2),
            "status": status
        }

        with self._lock:
            records = []
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        records = json.load(f)
                        if not isinstance(records, list):
                            records = []
                except Exception:
                    records = []

            # Append new record
            records.append(record)

            # Cap at MAX_TELEMETRY_RECORDS (FIFO prune)
            if len(records) > MAX_TELEMETRY_RECORDS:
                records = records[-MAX_TELEMETRY_RECORDS:]

            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️ Error saving telemetry record: {e}")

        return record

    def get_model_profile(self) -> Dict[str, Any]:
        """
        Calculate statistical weights and rolling averages from completed records.
        """
        records = [r for r in self.load_records() if r.get("status") == "completed"]
        sample_count = len(records)

        if sample_count < 3:
            return {
                "sample_count": sample_count,
                "is_cold_start": True,
                "fixed_overhead_s": 8.0,
                "avg_duration_ratio": 1.25,
                "size_penalty_ratio": 0.02,
                "rolling_api_latency_ms": 3000.0,
                "stage_weight_distribution": {
                    "audio_extraction": 0.05,
                    "speech_transcription": 0.30,
                    "lyric_refinement": 0.20,
                    "visual_generation": 0.10,
                    "media_encoding": 0.32,
                    "finalization": 0.03
                }
            }

        # Calculate ratios
        ratios = []
        api_latencies = []
        stage_totals: Dict[str, float] = {}

        for r in records:
            inp_dur = r.get("input_duration_s", 1.0)
            tot_dur = r.get("total_duration_s", 1.0)
            if inp_dur > 0 and tot_dur > 0:
                ratio = tot_dur / inp_dur
                # Clamp outliers
                ratios.append(min(4.0, max(0.5, ratio)))

            lat = r.get("api_latency_ms", 0.0)
            if lat > 0:
                api_latencies.append(min(15000.0, float(lat)))

            stage_durs = r.get("stage_durations", {})
            for stage_name, dur in stage_durs.items():
                stage_totals[stage_name] = stage_totals.get(stage_name, 0.0) + dur

        avg_ratio = sum(ratios) / len(ratios) if ratios else 1.5
        # Recent 10 API latencies (or fallback 3000ms)
        recent_latencies = api_latencies[-10:] if api_latencies else []
        avg_api_latency = (sum(recent_latencies) / len(recent_latencies)) if recent_latencies else 3000.0

        total_stage_time = sum(stage_totals.values())
        stage_weights = {}
        if total_stage_time > 0:
            for stage_name, val in stage_totals.items():
                stage_weights[stage_name] = round(val / total_stage_time, 3)
        else:
            stage_weights = {
                "audio_extraction": 0.05,
                "speech_transcription": 0.30,
                "lyric_refinement": 0.20,
                "visual_generation": 0.10,
                "media_encoding": 0.32,
                "finalization": 0.03
            }

        return {
            "sample_count": sample_count,
            "is_cold_start": False,
            "fixed_overhead_s": 8.0,
            "avg_duration_ratio": round(avg_ratio, 2),
            "size_penalty_ratio": 0.02,
            "rolling_api_latency_ms": round(avg_api_latency, 1),
            "stage_weight_distribution": stage_weights
        }

    def predict_duration(self, video_duration_s: float, video_size_mb: float = 0.0) -> float:
        """
        Predict render time in seconds for a video based on historical performance.
        Formula: max(12, int(fixed_overhead_s + (duration_s * avg_duration_ratio) + (size_mb * size_penalty_ratio)))
        """
        dur = max(1.0, float(video_duration_s))
        profile = self.get_model_profile()
        fixed_overhead = profile.get("fixed_overhead_s", 8.0)
        ratio = profile.get("avg_duration_ratio", 1.25)
        size_penalty = profile.get("size_penalty_ratio", 0.02)
        size_overhead = (float(video_size_mb) * size_penalty) if video_size_mb > 0 else 0.0

        if profile.get("is_cold_start", True):
            estimate = fixed_overhead + (dur * ratio) + size_overhead
        else:
            api_latency_s = profile.get("rolling_api_latency_ms", 3000.0) / 1000.0
            estimate = fixed_overhead + (dur * ratio) + size_overhead + (api_latency_s * 0.3)

        # Clamping: minimum 12s, maximum 6.0x duration (at least 30s)
        min_bound = 12.0
        max_bound = max(30.0, dur * 6.0)
        clamped_estimate = min(max_bound, max(min_bound, estimate))

        return round(clamped_estimate, 1)


# Global shared instance
telemetry_manager = TelemetryManager()


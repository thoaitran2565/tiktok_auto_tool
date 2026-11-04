# Contract Specification: Render Progress & Telemetry API

**Feature**: Granular Render Progress Tracking and Predictive Estimation  
**Branch**: `001-render-progress-prediction`  
**Date**: 2026-11-04  

---

## Overview

This contract documents the HTTP REST API endpoints that power real-time rendering stage updates, telemetry data persistence, and predictive duration estimations between the Flask backend and the web frontend.

---

## Endpoints

### 1. `GET /api/render-progress`

Returns the live progress of all queue items or a specific item, along with aggregated batch queue estimates.

#### Request
- **Method**: `GET`
- **Query Parameters**:
  - `id` *(optional, integer)*: If provided, returns state for that item specifically. If omitted, returns states for all actively tracking items.

#### Response: `200 OK`
```json
{
  "success": true,
  "queue_summary": {
    "total_items": 10,
    "completed_items": 3,
    "pending_items": 6,
    "failed_items": 0,
    "active_item_id": 4,
    "estimated_queue_remaining_s": 145.2
  },
  "progress": {
    "4": {
      "item_id": 4,
      "video_name": "sample_video.mp4",
      "status": "processing",
      "current_stage_id": "lyric_refinement",
      "current_stage_label": "Làm sạch lời bài hát AI",
      "percent": 45,
      "elapsed_s": 18.4,
      "estimated_total_s": 38.0,
      "estimated_remaining_s": 19.6,
      "stages": [
        {
          "id": "audio_extraction",
          "label": "Trích xuất âm thanh",
          "order": 1,
          "status": "completed",
          "duration_s": 1.2
        },
        {
          "id": "speech_transcription",
          "label": "Nhận diện giọng nói (Whisper)",
          "order": 2,
          "status": "completed",
          "duration_s": 8.4
        },
        {
          "id": "lyric_refinement",
          "label": "Làm sạch lời bài hát AI",
          "order": 3,
          "status": "active",
          "duration_s": 8.8
        },
        {
          "id": "visual_generation",
          "label": "Tạo hình ảnh & lyrics trong suốt",
          "order": 4,
          "status": "pending",
          "duration_s": 0.0
        },
        {
          "id": "media_encoding",
          "label": "Ghép video & mã hóa MP4",
          "order": 5,
          "status": "pending",
          "duration_s": 0.0
        },
        {
          "id": "finalization",
          "label": "Xác thực & dọn dẹp",
          "order": 6,
          "status": "pending",
          "duration_s": 0.0
        }
      ]
    }
  }
}
```

---

### 2. `GET /api/render-predictions`

Returns upfront duration estimates for all items currently queued in `session_data['queue']`.

#### Request
- **Method**: `GET`

#### Response: `200 OK`
```json
{
  "success": true,
  "is_cold_start": false,
  "telemetry_count": 24,
  "predictions": [
    {
      "id": 1,
      "video_name": "video_01.mp4",
      "duration_s": 25.5,
      "size_mb": 14.2,
      "estimated_total_s": 36.5,
      "confidence": "high"
    },
    {
      "id": 2,
      "video_name": "video_02.mp4",
      "duration_s": 60.0,
      "size_mb": 35.8,
      "estimated_total_s": 82.0,
      "confidence": "high"
    }
  ],
  "total_queue_estimate_s": 118.5
}
```

---

### 3. `GET /api/render-telemetry`

Provides aggregated statistics and recent history for telemetry metrics.

#### Request
- **Method**: `GET`
- **Query Parameters**:
  - `limit` *(optional, integer, default 10, max 100)*: Number of recent runs to return.

#### Response: `200 OK`
```json
{
  "success": true,
  "model_profile": {
    "sample_count": 24,
    "is_cold_start": false,
    "avg_duration_ratio": 1.25,
    "rolling_api_latency_ms": 2850,
    "stage_weight_distribution": {
      "audio_extraction": 0.05,
      "speech_transcription": 0.28,
      "lyric_refinement": 0.15,
      "visual_generation": 0.07,
      "media_encoding": 0.42,
      "finalization": 0.03
    }
  },
  "recent_records": [
    {
      "id": "tel_1730701000_1",
      "timestamp": "2026-11-04T15:20:00Z",
      "video_name": "sample.mp4",
      "input_duration_s": 30.0,
      "input_size_mb": 18.4,
      "total_duration_s": 38.2,
      "api_latency_ms": 2600,
      "status": "completed"
    }
  ]
}
```


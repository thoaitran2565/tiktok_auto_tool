# Contract Specification: Queue Management & Prediction API

**Feature**: Queue UX Refinements, Modal Image Picker, and Real-Duration Prediction  
**Branch**: `003-queue-ux-and-modal-picker`  
**Date**: 2026-11-04  

---

## 1. `POST /api/load-folders` (Enhanced with Probed Durations)

Scans input folders, probes actual video durations, and initializes the queue.

#### Request: `POST /api/load-folders`
```json
{
  "image_folder": "D:\\Media\\Images",
  "video_folder": "D:\\Media\\Videos"
}
```

#### Response: `200 OK`
```json
{
  "success": true,
  "available_images": ["bg1.png", "bg2.jpg", "chill.png"],
  "queue": [
    {
      "id": 1,
      "video_name": "intro.mp4",
      "video_path": "D:\\Media\\Videos\\intro.mp4",
      "duration_s": 18.5,
      "size_mb": 14.2,
      "image_name": "bg1.png",
      "image_path": "D:\\Media\\Images\\bg1.png",
      "status": "Chờ render"
    }
  ]
}
```

---

## 2. `POST /api/refresh-queue` (Non-Destructive Sync)

Refreshes folder contents without terminating or mutating ongoing render jobs.

#### Request: `POST /api/refresh-queue`
```json
{}
```

#### Response: `200 OK`
```json
{
  "success": true,
  "queue": [
    {
      "id": 1,
      "video_name": "intro.mp4",
      "status": "Đang render"
    },
    {
      "id": 2,
      "video_name": "new_clip.mp4",
      "duration_s": 42.0,
      "status": "Chờ render"
    }
  ],
  "new_items_added": 1,
  "active_item_id": 1
}
```

---

## 3. `POST /api/update-queue` (Image Swap)

Updates the selected image for a specific queue item before render starts.

#### Request: `POST /api/update-queue`
```json
{
  "id": 1,
  "image_name": "new_bg.jpg"
}
```

#### Response: `200 OK`
```json
{
  "success": true,
  "id": 1,
  "image_name": "new_bg.jpg",
  "image_path": "D:\\Media\\Images\\new_bg.jpg"
}
```

---

## 4. `GET /api/render-predictions` (Real-Duration Scaled)

Returns duration predictions calculated using real probed video duration.

#### Response: `200 OK`
```json
{
  "success": true,
  "is_cold_start": false,
  "predictions": [
    {
      "id": 1,
      "video_name": "intro.mp4",
      "duration_s": 18.5,
      "size_mb": 14.2,
      "estimated_total_s": 28
    }
  ],
  "total_queue_estimate_s": 28
}
```


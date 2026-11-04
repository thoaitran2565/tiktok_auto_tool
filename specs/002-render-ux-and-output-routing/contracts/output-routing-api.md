# Contract Specification: Output Routing & Media Serving API

**Feature**: Render UX Optimizations, Adaptive Queue Learning, and Output Routing  
**Branch**: `002-render-ux-and-output-routing`  
**Date**: 2026-11-04  

---

## 1. `POST /api/render-single` (Updated Response)

#### Response: `200 OK`
```json
{
  "success": true,
  "output_file": "CuocSongChill.mp4",
  "output_folder": "outputs",
  "has_lyrics": true,
  "video_url": "/outputs/CuocSongChill.mp4"
}
```

*When no lyrics are available:*
```json
{
  "success": true,
  "output_file": "CuocSongChill.mp4",
  "output_folder": "outputs-no-lyrics",
  "has_lyrics": false,
  "video_url": "/outputs-no-lyrics/CuocSongChill.mp4"
}
```

---

## 2. `GET /outputs-no-lyrics/<path:filename>`

Streams or serves the rendered video from the `outputs-no-lyrics` folder.

#### Response: `200 OK`
- **Content-Type**: `video/mp4`
- **Body**: Binary video stream

---

## 3. `GET /download/no-lyrics/<filename>`

Downloads the rendered video file as an attachment from `outputs-no-lyrics`.

#### Response: `200 OK`
- **Content-Disposition**: `attachment; filename="<filename>"`
- **Content-Type**: `video/mp4`


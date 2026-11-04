# Data Model: Render UX & Output Routing

**Feature**: Render UX Optimizations, Adaptive Queue Learning, and Output Routing  
**Branch**: `002-render-ux-and-output-routing`  
**Date**: 2026-11-04  

---

## 1. VideoRecord (Updated Database Entity)

Stored in `videos_db.json`. Updated to include output routing and lyrics classification:

```typescript
interface VideoRecord {
  id: string;                     // e.g. "vid_1730720000"
  filename: string;               // e.g. "BaiCaDatPhuongNam.mp4"
  path: string;                   // Absolute disk path
  output_folder: "outputs" | "outputs-no-lyrics"; // Target storage folder
  has_lyrics: boolean;            // True if AI successfully processed lyrics; False otherwise
  created_at: string;             // Format: "YYYY-MM-DD HH:MM:SS"
  status: "Chờ duyệt" | "Đã duyệt";
}
```

---

## 2. QueueItemState (Live UI Queue Model)

Represents an individual item in `session_data['queue']` and the frontend table view:

```typescript
interface QueueItemState {
  id: number;
  video_name: string;
  video_path: string;
  image_name: string;
  image_path: string;
  status: "Chờ render" | "Đang render" | "Hoàn thành" | "Lỗi";
  output_file?: string;
  output_folder?: "outputs" | "outputs-no-lyrics";
  has_lyrics?: boolean;
  estimated_total_s?: number;     // Integer seconds predicted
  elapsed_s?: number;             // Integer seconds elapsed
  current_stage_label?: string;
}
```

---

## 3. MediaModalState (Client-side Modal Inspector)

State managing the centered lightbox overlay:

```typescript
interface MediaModalState {
  isOpen: boolean;
  mediaType: "image" | "video";
  mediaUrl: string;
  title: string;
}
```

---

## 4. StageBoundaryDefinition (Progress Interpolation Ceilings)

Defines progress bar plateaus to avoid advancing past uncompleted stages:

| Stage ID | Label | Stage Weight | Cumulative Ceiling % |
|----------|-------|--------------|----------------------|
| `audio_extraction` | Trích xuất âm thanh | 10% | 10% |
| `speech_transcription` | Nhận diện giọng nói (Whisper) | 30% | 40% |
| `lyric_refinement` | Làm sạch lời bài hát AI | 20% | 60% |
| `visual_generation` | Tạo hình ảnh & lyrics | 10% | 70% |
| `media_encoding` | Ghép video & mã hóa MP4 | 25% | 95% |
| `finalization` | Xác thực & dọn dẹp | 5% | 100% |


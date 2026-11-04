# Data Model: Queue UX, Modal Picker & Real-Duration Prediction

**Feature**: Queue UX Refinements, Modal Image Picker, and Real-Duration Prediction  
**Branch**: `003-queue-ux-and-modal-picker`  
**Date**: 2026-11-04  

---

## 1. QueueItemState (Enhanced Live Model)

Represents an individual item in `session_data['queue']` on the backend and client-side `rawQueueData`:

```typescript
interface QueueItemState {
  id: number;
  video_name: string;
  video_path: string;
  duration_s: number;             // Probed actual video duration in seconds (NEW)
  size_mb: number;                // Input file size in Megabytes
  image_name: string;
  image_path: string;
  status: "Chờ render" | "Đang render" | "Hoàn thành" | "Lỗi";
  output_file?: string;
  output_folder?: "outputs" | "outputs-no-lyrics";
  has_lyrics?: boolean;
  estimated_total_s?: number;     // Predicted render duration in integer seconds
  elapsed_s?: number;
  current_stage_label?: string;
  is_locked?: boolean;            // True when status === "Hoàn thành" to disable controls (NEW)
}
```

---

## 2. ImagePickerState (Modal Curation Session)

Client-side state managing the interactive modal image picker:

```typescript
interface ImagePickerState {
  isOpen: boolean;
  activeItemId: number | null;
  originalImageName: string;      // Fallback if user cancels
  candidateImageName: string;     // Currently previewed candidate
  candidatePreviewUrl: string;    // Stream URL for high-res candidate preview
  availableImages: string[];      // Full list of images scanned from folder
}
```

---

## 3. SetupSectionState (Collapsible Folder Setup Bar)

Client UI state tracking the folder setup header visibility:

```typescript
interface SetupSectionState {
  isCollapsed: boolean;           // True once folders are scanned
  imageCount: number;             // Number of images detected in image folder
  videoCount: number;             // Number of videos detected in video folder
  imageFolderPath: string;
  videoFolderPath: string;
}
```

---

## 4. PredictiveModelParameters (Adaptive Duration Tuning)

Internal statistical parameters utilized by `TelemetryManager`:

```typescript
interface PredictiveModelParameters {
  fixed_overhead_s: number;       // Base overhead for AI model loading & pipeline setup (default: 8.0s)
  avg_duration_ratio: number;     // Render duration multiplier per media second (default: 1.25)
  size_penalty_ratio: number;     // Duration increment per MB (default: 0.02s/MB)
  sample_count: number;           // Number of completed renders used in rolling average
  is_cold_start: boolean;
}
```


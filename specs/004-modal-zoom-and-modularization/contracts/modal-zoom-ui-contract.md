# Interface Contract: Modal Image Wheel Zoom & Pan UI

**Feature**: Modal Image Wheel Zoom & Application Logic Decoupling  
**Date**: 2026-11-04  
**Scope**: Client-side UI & DOM Contracts (`templates/index.html`)  

## 1. DOM Structure & Target Elements

The zoom functionality attaches to:
1. `#modalCandidateImg` inside `.modal-preview-stage` (curation modal).
2. `#mediaModalBody img` inside `#mediaModal` (lightbox viewer modal).

### Stage Structure:
```html
<div class="modal-preview-stage" id="modalPreviewStage" style="overflow: hidden; position: relative;">
    <img id="modalCandidateImg" src="..." alt="...">
    <!-- Zoom Level Pill Indicator -->
    <div id="modalZoomBadge" class="modal-zoom-badge" style="display: none;">100%</div>
    <!-- Quick Reset Control -->
    <button id="modalZoomResetBtn" class="modal-zoom-reset-btn" style="display: none;" title="Khôi phục kích thước ban đầu (Nhấp đúp)">
        <i class="fa-solid fa-arrows-rotate"></i>
    </button>
</div>
```

---

## 2. Event Listener Contracts

| Event | Target | Handler Behavior |
|---|---|---|
| `wheel` | Container / Image | `e.preventDefault()`. Calculate delta. Multiply scale by `1 - e.deltaY * 0.0015`. Clamp `[1.0, 5.0]`. If scale becomes 1.0, reset offsets to 0. Update CSS transform. |
| `mousedown` | Image (`scale > 1.05`) | Set `isDragging = true`, record `startX = e.clientX - translateX`, `startY = e.clientY - translateY`. Change cursor to `grabbing`. |
| `mousemove` | Window / Stage | If `isDragging`: update `translateX = e.clientX - startX`, `translateY = e.clientY - startY`. Apply transform. |
| `mouseup` / `mouseleave` | Window / Stage | Set `isDragging = false`. Restore cursor to `grab` or default. |
| `dblclick` | Image | Trigger `resetZoom()`. Smoothly animate back to scale 1.0 and offset (0, 0). |

---

## 3. CSS Transform Contract

Applied directly via inline style or CSS class:
```css
transform: translate3d(${translateX}px, ${translateY}px, 0) scale(${scale});
transform-origin: center center;
transition: transform 0.05s ease-out; /* Smooth responsive interpolation */
cursor: ${scale > 1.05 ? (isDragging ? 'grabbing' : 'grab') : 'zoom-in'};
```

---

## 4. Reset Lifecycle Hooks

The method `resetModalZoom()` MUST be called automatically by:
- `openImagePickerModal(itemId)`
- `selectCandidateImage(imgName)`
- `pickRandomImage()`
- `closeMediaModal()`
- Double-clicking the preview image or clicking `#modalZoomResetBtn`.


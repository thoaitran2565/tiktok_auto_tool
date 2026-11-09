# Interface Contract: Multi-Image UI & DOM Components

**Feature**: Multi-Image Video Slideshow with Smooth Transitions  
**Date**: 2026-11-04  
**Scope**: Client-Side DOM Contracts (`templates/index.html`)  

## 1. Column 2 (Ảnh Ghép Mẫu) Layout & Controls

For each row in `#queueTable`:

```html
<td class="col-image-config">
    <!-- Toggle Switch: Ghép nhiều ảnh -->
    <div class="multi-image-toggle-bar">
        <label class="switch-sm" title="Bật/Tắt tạo video chạy nhiều ảnh">
            <input type="checkbox" id="multi-toggle-${item.id}" ${item.is_multi_image ? 'checked' : ''} onchange="toggleMultiImageMode(${item.id})">
            <span class="slider-sm round"></span>
        </label>
        <span class="toggle-label">Nhiều ảnh</span>
    </div>

    <!-- Mode 1: Single Image Mode (default) -->
    <div id="single-image-box-${item.id}" style="${item.is_multi_image ? 'display: none;' : 'display: flex;'}">
        <img class="img-preview-thumb" src="..." onclick="openImagePickerModal(${item.id})">
        <span class="img-name-label">${item.image_name}</span>
    </div>

    <!-- Mode 2: Multi-Image Mode -->
    <div id="multi-image-box-${item.id}" style="${item.is_multi_image ? 'display: flex;' : 'display: none;'}">
        <!-- Stepper: [-] 10 [+] -->
        <div class="stepper-controls">
            <button class="btn-step" onclick="adjustImageCount(${item.id}, -1)">-</button>
            <span class="stepper-count-badge" id="stepper-count-${item.id}">${item.image_count || 10} ảnh</span>
            <button class="btn-step" onclick="adjustImageCount(${item.id}, 1)">+</button>
        </div>
        <!-- Stacked preview thumbnails or button to view multi-image gallery -->
        <div class="multi-thumb-stack" onclick="openMultiImagePickerModal(${item.id})" title="Xem và tùy chỉnh danh sách ảnh">
            <!-- First 3 overlapping thumbnail pills + count badge -->
            <span class="badge-slideshow"><i class="fa-solid fa-layer-group"></i> Tùy chỉnh ${item.image_count || 10} ảnh</span>
        </div>
    </div>
</td>
```

---

## 2. Modal Multi-Image Curation Stage

When opening modal for an item with `is_multi_image == true`:
- Modal Title: `Quản lý bộ ảnh chạy Slideshow (${count} ảnh)`
- Toolbar:
  - Button "Đổi ngẫu nhiên bộ ảnh" (`rerollMultiImageBatch()`).
  - Button "Thêm 1 ảnh" (`addSlotToMultiImage()`).
  - Button "Xác nhận áp dụng".
- Gallery Grid:
  - Displays ordered numbered cards ($1, 2, 3 \dots N$).
  - Each card displays the image thumbnail, filename, a "Thay đổi" button, and a "Xóa" button (if $N > 2$).
  - Clicking "Thay đổi" on slot $k$ opens the candidate selection strip below to swap image $k$.


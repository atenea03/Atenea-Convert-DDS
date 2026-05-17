<div align="center">

# 🖼️ Atenea DDS Converter

**Convert textures between DDS and multiple image formats, optimized with Mipmap generation and compression profiles for FiveM.**
No internet connection required. Just open, select, and convert.

![Version](https://img.shields.io/badge/version-v2026-F5A800?style=flat-square&labelColor=1a1a1a)
![Platform](https://img.shields.io/badge/platform-Windows-blue?style=flat-square&labelColor=1a1a1a)
![License](https://img.shields.io/badge/license-Atenea_Store_Tools-F5A800?style=flat-square&labelColor=1a1a1a)

</div>

---

## 📦 Folder Contents

| File / Folder | Description |
|---|---|
| `Ate_Convert_dds.exe` | ✅ The main program. Double-click to open. |
| `Ate_Convert_dds.py` | Source code (developers only). |
| `texconv.exe` | Microsoft DirectXTex tool. **Required in the same folder** for DDS processing. |
| `logo.ico` / `logo.png` | Application icon and visual branding files. |

> ⚠️ **Do not move or delete any file or utility.**
> The program requires `texconv.exe` and the asset files in its original location to run and process compression correctly.

---

## 🚀 How to Use

**Step 1 — Open the program**
- Double-click `Ate_Convert_dds.exe`.
- The Atenea interface will open with a dark background, dynamic layouts, and a golden logo.

**Step 2 — Select conversion mode**
- By default, the app opens in **Image → DDS** mode.
- Click the **⇄ Switch to...** button at the top right to instantly toggle between **Image → DDS** or **DDS → Image** layouts.

**Step 3 — Select input files or folders**
- **📁 Folder** → Automatically scans all matching textures inside a directory.
- **📄 Files** → Allows you to cherry-pick individual files manually.
- *(Image → DDS only)*: Use **Filter by format** to target specific extensions (`PNG`, `JPG`, etc.) or select `All formats`.

**Step 4 — Select output folder**
- Click the **…** button under Output Folder to set a destination.
- Default names are automatically managed (`dds_output` or `img_output`), and missing folders will be generated instantly.

**Step 5 — Configure texture settings**
- **In Image → DDS mode:**
  - Select your preferred compression profile (**Auto**, **BC3/DXT5**, **BC1/DXT1**, **BC7**, or **BC4**).
  - Toggle **Generate Mipmaps** on/off *(Highly recommended for FiveM optimization)*.
- **In DDS → Image mode:**
  - Simply select your target export format button (`PNG`, `JPG`, `WEBP`, `BMP`, `TIFF`).

**Step 6 — Convert**
- Click the bottom **Convert** button.
- The real-time progress bar and file counters will track the conversion queue.
- Once finished, a summary popup will display total successful conversions and any logged errors.

---

## ⚙️ How Compression & Conversion Works

### 🔹 Image → DDS Mode
- **Auto Mode (Recommended):** The program automatically analyzes transparency. If the image has alpha channels, it uses **BC3 (DXT5)**; if it is fully opaque, it applies **BC1 (DXT1)** to maximize VRAM performance.
- **Mipmaps:** When active, downscaled sub-textures are baked directly into the `.dds` file to eliminate aliasing and optimize texture rendering distances inside the GTA V engine.

### 🔹 DDS → Image Mode
- Uses an automated two-step extraction chain: decompresses the hardware-encoded DDS surface into a raw buffer via `texconv` and translates it into standard raster arrays using Pillow.

---

## 🗂️ Supported Formats & Compression Perfiles

### Output Standard Images
| Format | Extensions | Notes |
|--------|------------|-------|
| PNG | `.png` | Lossless. Pure transparency mapping. |
| JPG | `.jpg` / `.jpeg` | Standard compressed textures. Alpha channels automatically drop to solid black/white. |
| WEBP | `.webp` | Modern web compression format with alpha transparency support. |
| BMP | `.bmp` | Windows Bitmap raw format. Uncompressed. |
| TIFF | `.tiff` / `.tif` | Tagged Image File Format. Maximum archive quality. |

### DDS Compression Profiles (DirectX)
| Profile | Suggested Use Case | Technical Behavior |
|--------|------------|-------|
| **Auto** | General Stream Assets | Dynamically switches profiles depending on asset alpha transparency. |
| **BC3 / DXT5** | Clothing, Hair, Custom Props | Block compression with high-quality explicit 4-bit alpha channels. |
| **BC1 / DXT1** | Terrains, Buildings, Posters | High compression ratio without alpha channels. Perfect for solid surfaces. |
| **BC7** | HD Cars, Weapons, Badges | Advanced high-fidelity texture profile. Preserves high-frequency color profiles. |
| **BC4** | Normal/Specular/Roughness | Grayscale channel extraction. Ideal for material shaders. |

---

## 💡 Tips

- **FiveM Stream Optimization:** Always keep **Generate Mipmaps** active when converting assets for game environments to avoid visual shimmering and server texture load stutters.
- **VRAM Savings:** Use the **Auto** setting or manually select **BC1/DXT1** for non-transparent elements like flooring or walls to drastically cut down asset sizes.
- **Batch Processing:** Drop full folders with miscellaneous files; the application filters out irrelevant extensions automatically without throwing execution interruptions.

---

<div align="center">

© 2026 **Atenea Store Tools**

</div>


Discord: https://discord.gg/mam8Nmg49d

**IMAGES:**

![1](https://i.imgur.com/yQi7Ala.png)

![2](https://i.imgur.com/O1REYdI.png)

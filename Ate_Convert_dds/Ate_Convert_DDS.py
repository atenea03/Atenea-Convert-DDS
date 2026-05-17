import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk

# ==========================================================
# PALETTE
# ==========================================================
BG_BASE      = "#1a1a1a"
BG_PANEL     = "#232323"
BG_ELEVATED  = "#2c2c2c"
BG_ACTIVE    = "#383838"
BORDER       = "#3a3a3a"
TEXT_PRIMARY = "#f0f0f0"
TEXT_MUTED   = "#888888"
TEXT_GOLD    = "#F5A800"
BTN_HOVER    = "#3a3a3a"
WHITE        = "#ffffff"

# ==========================================================
# FORMATS
# ==========================================================
INPUT_FORMATS_IMG = ["All formats", "PNG", "JPG", "WEBP", "BMP", "TIFF"]
EXT_MAP_IMG = {
    "PNG":         [".png"],
    "JPG":         [".jpg", ".jpeg"],
    "WEBP":        [".webp"],
    "BMP":         [".bmp"],
    "TIFF":        [".tiff", ".tif"],
    "All formats": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"],
}

DDS_OUT_FORMATS = {
    "Auto":     "AUTO",
    "BC3/DXT5": "BC3_UNORM",
    "BC1/DXT1": "BC1_UNORM",
    "BC7":      "BC7_UNORM",
    "BC4":      "BC4_UNORM",
}

IMG_OUT_FORMATS = ["PNG", "JPG", "WEBP", "BMP", "TIFF"]
PIL_EXT = {"PNG": ".png", "JPG": ".jpg", "WEBP": ".webp", "BMP": ".bmp", "TIFF": ".tiff"}
PIL_SAVE = {"PNG": "PNG", "JPG": "JPEG", "WEBP": "WEBP", "BMP": "BMP", "TIFF": "TIFF"}

# ==========================================================
# CONVERSION LOGIC
# ==========================================================
def has_alpha(path):
    try:
        img = Image.open(path).convert("RGBA")
        _, _, _, a = img.split()
        return a.getextrema()[0] < 255
    except Exception:
        return False


def convert_to_dds(inputs, output_folder, fmt_dds, mipmaps,
                   cb_prog, cb_log, cb_fin, texconv_path):
    os.makedirs(output_folder, exist_ok=True)
    total = len(inputs)
    ok = errors = 0
    for i, path in enumerate(inputs):
        name = os.path.basename(path)
        base = os.path.splitext(name)[0]
        dest = os.path.join(output_folder, base + ".dds")
        try:
            fmt_use = fmt_dds
            if fmt_use == "AUTO":
                fmt_use = "BC3_UNORM" if has_alpha(path) else "BC1_UNORM"
                cb_log(f"  ·  {name}  →  auto: {fmt_use}\n")
            cmd = [texconv_path, "-nologo", "-y", "-f", fmt_use, "-o", output_folder]
            cmd += ["-m", "0"] if mipmaps else ["-m", "1"]
            cmd.append(path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(dest):
                ok += 1
                cb_log(f"  ✓  {name}  →  {base}.dds\n")
            else:
                raise RuntimeError(result.stderr.strip() or "texconv failed")
        except Exception as e:
            errors += 1
            cb_log(f"  ✗  {name}: {e}\n")
        cb_prog(i + 1, total)
    cb_fin(ok, errors)


def convert_dds_to_img(inputs, output_folder, out_fmt,
                       cb_prog, cb_log, cb_fin, texconv_path):
    os.makedirs(output_folder, exist_ok=True)
    total = len(inputs)
    ok = errors = 0
    for i, path in enumerate(inputs):
        name = os.path.basename(path)
        base = os.path.splitext(name)[0]
        ext  = PIL_EXT[out_fmt]
        dest = os.path.join(output_folder, base + ext)
        try:
            # Step 1: texconv → PNG
            cmd = [texconv_path, "-nologo", "-y", "-ft", "png", "-o", output_folder, path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            png_out = os.path.join(output_folder, base + ".png")
            if result.returncode != 0 or not os.path.exists(png_out):
                raise RuntimeError(result.stderr.strip() or "texconv failed")
            # Step 2: Pillow → final format
            if out_fmt != "PNG":
                img = Image.open(png_out)
                if out_fmt == "JPG":
                    img = img.convert("RGB")
                img.save(dest, PIL_SAVE[out_fmt])
                os.remove(png_out)
            ok += 1
            cb_log(f"  ✓  {name}  →  {base}{ext}\n")
        except Exception as e:
            errors += 1
            cb_log(f"  ✗  {name}: {e}\n")
        cb_prog(i + 1, total)
    cb_fin(ok, errors)


# ==========================================================
# APP
# ==========================================================
class AteneaDDSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Atenea DDS Converter")
        self.configure(fg_color=BG_BASE)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        win_w = max(480, min(int(sw * 0.38), 820))
        win_h = max(560, min(int(sh * 0.80), 900))
        cx = (sw - win_w) // 2
        cy = (sh - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{cx}+{cy}")
        self.minsize(480, 560)
        self.resizable(True, True)

        self._sc = max(0.72, min(sw / 1920, 1.3))

        self.selected_files  = []
        self._total          = 0
        self._active_dds_fmt = "AUTO"
        self._active_img_fmt = "PNG"
        self._mipmaps        = True
        self._mode           = "TO_DDS"

        self._set_icon()
        self._build_ui()

    def _fs(self, s): return max(7, int(s * self._sc))
    def _pad(self, s): return max(3, int(s * self._sc))
    def _h(self, s):  return max(24, int(s * self._sc))

    def _set_icon(self):
        for path, method in [
            (self._res("logo.ico"), "bitmap"),
            (self._res("logo.png"), "photo"),
        ]:
            if not os.path.exists(path):
                continue
            try:
                if method == "bitmap":
                    self.iconbitmap(path)
                else:
                    self.iconphoto(True, ImageTk.PhotoImage(Image.open(path)))
            except Exception:
                pass

    # ── UI ───────────────────────────────────────────────────
    def _build_ui(self):
        p  = self._pad
        h  = self._h
        fs = self._fs

        root = ctk.CTkFrame(self, fg_color=BG_BASE)
        root.pack(fill="both", expand=True)

        # ── SHARED: HEADER ───────────────────────────────────
        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x", padx=p(24), pady=(p(10), p(2)))

        logo_path = self._res("logo.png")
        if os.path.exists(logo_path):
            try:
                li = ctk.CTkImage(Image.open(logo_path), size=(h(42), h(42)))
                ctk.CTkLabel(header, image=li, text="").pack(side="left", padx=(0, p(10)))
            except Exception:
                pass

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_col, text="Atenea DDS Converter",
                     font=("Segoe UI Semibold", fs(18)),
                     text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Atenea Store Tools  ·  V2026",
                     font=("Segoe UI", fs(10)),
                     text_color=TEXT_GOLD).pack(anchor="w")

        self.btn_mode = ctk.CTkButton(
            header, text="⇄  Switch to DDS → Image",
            font=("Segoe UI", fs(10)),
            fg_color=BG_ELEVATED, hover_color=BTN_HOVER,
            text_color=TEXT_GOLD,
            border_width=1, border_color=BORDER,
            height=h(28), corner_radius=8,
            command=self._toggle_mode,
        )
        self.btn_mode.pack(side="right")

        # ── SHARED: TEXCONV ──────────────────────────────────
        self._hdivider(root)
        self._hlabel(root, "TEXCONV.EXE")

        tc_row = ctk.CTkFrame(root, fg_color="transparent")
        tc_row.pack(fill="x", padx=p(24))
        tc_row.columnconfigure(0, weight=1)

        self.entry_texconv = ctk.CTkEntry(
            tc_row, height=h(30), corner_radius=8,
            fg_color=BG_PANEL, border_color=BORDER, border_width=1,
            placeholder_text="Path to texconv.exe…",
            placeholder_text_color=TEXT_MUTED,
            text_color=TEXT_PRIMARY, font=("Segoe UI", fs(11)),
        )
        auto = self._res("texconv.exe")
        if os.path.exists(auto):
            self.entry_texconv.insert(0, auto)
        self.entry_texconv.grid(row=0, column=0, sticky="ew", padx=(0, p(8)))
        ctk.CTkButton(
            tc_row, text="…", width=h(30), height=h(30), corner_radius=8,
            fg_color=BG_ELEVATED, hover_color=BTN_HOVER,
            text_color=TEXT_PRIMARY, font=("Segoe UI", fs(13)),
            border_width=1, border_color=BORDER,
            command=self.select_texconv,
        ).grid(row=0, column=1)

        ctk.CTkLabel(root,
            text="  Download texconv.exe from: github.com/microsoft/DirectXTex",
            font=("Segoe UI", fs(8)), text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=p(24), pady=(p(2), 0))

        # ── SHARED: INPUT ────────────────────────────────────
        self._hdivider(root)
        self.lbl_input = self._hlabel(root, "INPUT  ( Image → DDS )")

        self.entry_in = ctk.CTkEntry(
            root, height=h(30), corner_radius=8,
            fg_color=BG_PANEL, border_color=BORDER, border_width=1,
            placeholder_text="Select a folder or files…",
            placeholder_text_color=TEXT_MUTED,
            text_color=TEXT_PRIMARY, font=("Segoe UI", fs(11)),
        )
        self.entry_in.pack(fill="x", padx=p(24), pady=(0, p(5)))

        io_row = ctk.CTkFrame(root, fg_color="transparent")
        io_row.pack(fill="x", padx=p(24))
        io_row.columnconfigure(0, weight=1)
        io_row.columnconfigure(1, weight=1)
        self._grid_btn(io_row, "Folder", self.select_folder, 0)
        self._grid_btn(io_row, "Files",  self.select_files,  1)

        # ── SHARED: OUTPUT FOLDER ────────────────────────────
        self._hdivider(root)
        self._hlabel(root, "OUTPUT FOLDER")

        out_row = ctk.CTkFrame(root, fg_color="transparent")
        out_row.pack(fill="x", padx=p(24))
        out_row.columnconfigure(0, weight=1)

        self.entry_out = ctk.CTkEntry(
            out_row, height=h(30), corner_radius=8,
            fg_color=BG_PANEL, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, font=("Segoe UI", fs(11)),
        )
        self.entry_out.insert(0, "dds_output")
        self.entry_out.grid(row=0, column=0, sticky="ew", padx=(0, p(8)))
        ctk.CTkButton(
            out_row, text="…", width=h(30), height=h(30), corner_radius=8,
            fg_color=BG_ELEVATED, hover_color=BTN_HOVER,
            text_color=TEXT_PRIMARY, font=("Segoe UI", fs(13)),
            border_width=1, border_color=BORDER,
            command=self.select_out,
        ).grid(row=0, column=1)

        # 📦 CONTENEDOR DINÁMICO CENTRAL (Evita que el layout colapse al cambiar de modo)
        self.dynamic_body = ctk.CTkFrame(root, fg_color="transparent")
        self.dynamic_body.pack(fill="x")

        # ── MODE FRAME: Image → DDS ──────────────────────────
        self.frame_to_dds = ctk.CTkFrame(self.dynamic_body, fg_color="transparent")

        self._hdivider(self.frame_to_dds)
        self._hlabel(self.frame_to_dds, "FILTER BY FORMAT")
        self.fmt_entrada = ctk.CTkOptionMenu(
            self.frame_to_dds, values=INPUT_FORMATS_IMG,
            height=h(30), corner_radius=8,
            fg_color=BG_PANEL, button_color=BG_ELEVATED,
            button_hover_color=BTN_HOVER, text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_PANEL, dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=BG_ELEVATED,
            font=("Segoe UI", fs(11)), dropdown_font=("Segoe UI", fs(11)),
        )
        self.fmt_entrada.set("All formats")
        self.fmt_entrada.pack(fill="x", padx=p(24))

        self._hdivider(self.frame_to_dds)
        self._hlabel(self.frame_to_dds, "DDS FORMAT")

        self.dds_buttons = {}
        dds_fmt_row = ctk.CTkFrame(self.frame_to_dds, fg_color="transparent")
        dds_fmt_row.pack(fill="x", padx=p(24))
        keys = list(DDS_OUT_FORMATS.keys())
        for i in range(len(keys)):
            dds_fmt_row.columnconfigure(i, weight=1)
        for i, (label, val) in enumerate(DDS_OUT_FORMATS.items()):
            active = (val == "AUTO")
            btn = ctk.CTkButton(
                dds_fmt_row, text=label,
                height=h(28), corner_radius=8,
                fg_color=BG_ACTIVE if active else BG_ELEVATED,
                hover_color=BTN_HOVER,
                text_color=WHITE if active else TEXT_PRIMARY,
                border_width=1,
                border_color="#555555" if active else BORDER,
                font=("Segoe UI", fs(10)),
                command=lambda v=val: self._select_dds_fmt(v),
            )
            btn.grid(row=0, column=i, sticky="ew", padx=(0, p(5) if i < len(keys)-1 else 0))
            self.dds_buttons[val] = btn

        self.fmt_desc = ctk.CTkLabel(
            self.frame_to_dds,
            text="  Auto: BC3 with alpha, BC1 without  —  recommended for FiveM",
            font=("Segoe UI", fs(8)), text_color=TEXT_MUTED,
        )
        self.fmt_desc.pack(anchor="w", padx=p(24), pady=(p(3), 0))

        self._hdivider(self.frame_to_dds)
        mip_row = ctk.CTkFrame(self.frame_to_dds, fg_color="transparent")
        mip_row.pack(fill="x", padx=p(24), pady=(0, p(3)))
        mip_info = ctk.CTkFrame(mip_row, fg_color="transparent")
        mip_info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(mip_info, text="Generate Mipmaps",
                     font=("Segoe UI", fs(11)), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(mip_info, text="Required for FiveM textures",
                     font=("Segoe UI", fs(8)), text_color=TEXT_MUTED).pack(anchor="w")
        self.mip_switch = ctk.CTkSwitch(
            mip_row, text="",
            onvalue=True, offvalue=False,
            fg_color=BG_ELEVATED, progress_color=BG_ACTIVE,
            button_color=TEXT_PRIMARY, button_hover_color=WHITE,
            command=self._on_mip_toggle,
        )
        self.mip_switch.select()
        self.mip_switch.pack(side="right")

        # Se muestra este frame por defecto
        self.frame_to_dds.pack(fill="x")

        # ── MODE FRAME: DDS → Image ──────────────────────────
        self.frame_to_img = ctk.CTkFrame(self.dynamic_body, fg_color="transparent")

        self._hdivider(self.frame_to_img)
        self._hlabel(self.frame_to_img, "OUTPUT FORMAT")

        self.img_out_buttons = {}
        img_fmt_row = ctk.CTkFrame(self.frame_to_img, fg_color="transparent")
        img_fmt_row.pack(fill="x", padx=p(24))
        for i in range(len(IMG_OUT_FORMATS)):
            img_fmt_row.columnconfigure(i, weight=1)
        for i, fmt in enumerate(IMG_OUT_FORMATS):
            active = (fmt == "PNG")
            btn = ctk.CTkButton(
                img_fmt_row, text=fmt,
                height=h(28), corner_radius=8,
                fg_color=BG_ACTIVE if active else BG_ELEVATED,
                hover_color=BTN_HOVER,
                text_color=WHITE if active else TEXT_PRIMARY,
                border_width=1,
                border_color="#555555" if active else BORDER,
                font=("Segoe UI", fs(10)),
                command=lambda f=fmt: self._select_img_fmt(f),
            )
            btn.grid(row=0, column=i, sticky="ew", padx=(0, p(5) if i < len(IMG_OUT_FORMATS)-1 else 0))
            self.img_out_buttons[fmt] = btn

        # ── SHARED: STATUS + LOG + PROGRESS + BUTTON ─────────
        self._hdivider(root)

        status_row = ctk.CTkFrame(root, fg_color="transparent")
        status_row.pack(fill="x", padx=p(24), pady=(p(1), p(3)))
        ctk.CTkLabel(status_row, text="·",
                     font=("Segoe UI", fs(12)), text_color=TEXT_MUTED).pack(side="left")
        self.status_text = ctk.CTkLabel(
            status_row, text="Ready",
            font=("Segoe UI", fs(9)), text_color=TEXT_MUTED)
        self.status_text.pack(side="left", padx=(p(3), 0))
        self.counter_label = ctk.CTkLabel(
            status_row, text="0 / 0",
            font=("Segoe UI", fs(9)), text_color=TEXT_MUTED)
        self.counter_label.pack(side="right")

        self.log_box = ctk.CTkTextbox(
            root, height=h(80), corner_radius=8,
            fg_color=BG_PANEL, border_color=BORDER, border_width=1,
            text_color=TEXT_MUTED, font=("Consolas", fs(10)),
            scrollbar_button_color=BG_ELEVATED,
        )
        self.log_box.pack(fill="x", padx=p(24), pady=(0, p(4)))
        self.log_box.configure(state="normal")
        self.log_box.insert("end", "  —  Waiting for input…\n")
        self.log_box.configure(state="disabled")

        self.progress_bar = ctk.CTkProgressBar(
            root, height=3, corner_radius=2,
            fg_color=BG_ELEVATED, progress_color=TEXT_PRIMARY,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=p(24), pady=(0, p(6)))

        self.btn_convert = ctk.CTkButton(
            root, text="Convert",
            font=("Segoe UI Semibold", fs(13)),
            fg_color=BG_ELEVATED, hover_color=BTN_HOVER,
            text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER,
            height=h(40), corner_radius=8,
            command=self.start_convert,
        )
        self.btn_convert.pack(fill="x", padx=p(24), pady=(0, p(3)))

        ctk.CTkLabel(root, text="© 2026  Atenea Store Tools",
                     font=("Segoe UI", fs(8)), text_color=TEXT_MUTED).pack(pady=(p(1), p(8)))

    # ── MODE TOGGLE ──────────────────────────────────────────
    def _toggle_mode(self):
        self.selected_files = []
        self.entry_in.delete(0, tk.END)
        self._log_clear()
        self.status_text.configure(text="Ready", text_color=TEXT_MUTED)
        self.progress_bar.set(0)
        self.counter_label.configure(text="0 / 0")

        if self._mode == "TO_DDS":
            self._mode = "TO_IMG"
            self.btn_mode.configure(text="⇄  Switch to Image → DDS")
            self.lbl_input.configure(text="INPUT  ( DDS → Image )")
            self.entry_in.configure(placeholder_text="Select DDS files or folder…")
            self.entry_out.delete(0, tk.END)
            self.entry_out.insert(0, "img_output")
            self.frame_to_dds.pack_forget()
            self.frame_to_img.pack(fill="x")
        else:
            self._mode = "TO_DDS"
            self.btn_mode.configure(text="⇄  Switch to DDS → Image")
            self.lbl_input.configure(text="INPUT  ( Image → DDS )")
            self.entry_in.configure(placeholder_text="Select a folder or files…")
            self.entry_out.delete(0, tk.END)
            self.entry_out.insert(0, "dds_output")
            self.frame_to_img.pack_forget()
            self.frame_to_dds.pack(fill="x")

    # ── HELPERS ──────────────────────────────────────────────
    def _hdivider(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", padx=self._pad(24), pady=(self._pad(4), self._pad(4)))

    def _hlabel(self, parent, text):
        lbl = ctk.CTkLabel(parent, text=text,
                           font=("Segoe UI", self._fs(8), "bold"),
                           text_color=TEXT_MUTED)
        lbl.pack(anchor="w", padx=self._pad(24), pady=(0, self._pad(3)))
        return lbl

    def _grid_btn(self, parent, text, command, col):
        ctk.CTkButton(
            parent, text=text,
            height=self._h(30), corner_radius=8,
            fg_color=BG_ELEVATED, hover_color=BTN_HOVER,
            text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER,
            font=("Segoe UI", self._fs(11)),
            command=command,
        ).grid(row=0, column=col, sticky="ew",
               padx=(0, self._pad(5) if col == 0 else 0))

    # ── FORMAT SELECTORS ─────────────────────────────────────
    _dds_descriptions = {
        "AUTO":      "Auto: BC3 with alpha, BC1 without  —  recommended for FiveM",
        "BC3_UNORM": "BC3 / DXT5: compression with transparency. For clothing, props...",
        "BC1_UNORM": "BC1 / DXT1: compression without alpha. For backgrounds, floors...",
        "BC7_UNORM": "BC7: maximum quality, larger file. For high-definition textures.",
        "BC4_UNORM": "BC4: grayscale / roughness and metallic maps.",
    }

    def _select_dds_fmt(self, val):
        for v, btn in self.dds_buttons.items():
            if v == val:
                btn.configure(fg_color=BG_ACTIVE, text_color=WHITE, border_color="#555555")
            else:
                btn.configure(fg_color=BG_ELEVATED, text_color=TEXT_PRIMARY, border_color=BORDER)
        self._active_dds_fmt = val
        self.fmt_desc.configure(text="  " + self._dds_descriptions.get(val, ""))

    def _select_img_fmt(self, fmt):
        for f, btn in self.img_out_buttons.items():
            if f == fmt:
                btn.configure(fg_color=BG_ACTIVE, text_color=WHITE, border_color="#555555")
            else:
                btn.configure(fg_color=BG_ELEVATED, text_color=TEXT_PRIMARY, border_color=BORDER)
        self._active_img_fmt = fmt

    def _on_mip_toggle(self):
        self._mipmaps = self.mip_switch.get()

    # ── FILE SELECTION ───────────────────────────────────────
    def select_texconv(self):
        f = filedialog.askopenfilename(
            title="Select texconv.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if f:
            self.entry_texconv.delete(0, tk.END)
            self.entry_texconv.insert(0, f)

    def select_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.selected_files = []
            self.entry_in.delete(0, tk.END)
            self.entry_in.insert(0, f)

    def select_files(self):
        if self._mode == "TO_DDS":
            ftypes = [("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif"),
                      ("All files", "*.*")]
        else:
            ftypes = [("DDS files", "*.dds"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Select files", filetypes=ftypes)
        if files:
            self.selected_files = list(files)
            n = len(files)
            self.entry_in.delete(0, tk.END)
            self.entry_in.insert(0, f"{n} file{'s' if n != 1 else ''} selected")

    def select_out(self):
        f = filedialog.askdirectory()
        if f:
            self.entry_out.delete(0, tk.END)
            self.entry_out.insert(0, f)

    # ── GET INPUT FILES ──────────────────────────────────────
    def _get_inputs(self):
        exts = EXT_MAP_IMG[self.fmt_entrada.get()] if self._mode == "TO_DDS" else [".dds"]
        if self.selected_files:
            return [f for f in self.selected_files
                    if os.path.splitext(f)[1].lower() in exts]
        folder = self.entry_in.get().strip()
        if not folder or not os.path.isdir(folder):
            return []
        return [os.path.join(folder, f) for f in os.listdir(folder)
                if os.path.splitext(f)[1].lower() in exts]

    # ── CONVERT ──────────────────────────────────────────────
    def start_convert(self):
        texconv = self.entry_texconv.get().strip()
        out     = self.entry_out.get().strip()
        files   = self._get_inputs()

        if not texconv or not os.path.exists(texconv):
            messagebox.showerror("texconv.exe not found",
                "Please select the path to texconv.exe.\n"
                "Download it from: github.com/microsoft/DirectXTex/releases")
            return
        if not files:
            messagebox.showerror("No files found", "No files found with the selected format.")
            return
        if not out:
            messagebox.showerror("Missing output", "Please select an output folder.")
            return

        self._total = len(files)
        self.progress_bar.set(0)
        self.counter_label.configure(text=f"0 / {self._total}")
        self._log_clear()
        self.status_text.configure(text="Converting…", text_color=TEXT_PRIMARY)
        self.btn_convert.configure(state="disabled", text="Converting…")

        if self._mode == "TO_DDS":
            threading.Thread(
                target=convert_to_dds,
                args=(files, out, self._active_dds_fmt, self._mipmaps,
                      self._cb_prog, self._cb_log, self._cb_fin, texconv),
                daemon=True,
            ).start()
        else:
            threading.Thread(
                target=convert_dds_to_img,
                args=(files, out, self._active_img_fmt,
                      self._cb_prog, self._cb_log, self._cb_fin, texconv),
                daemon=True,
            ).start()

    # ── CALLBACKS ────────────────────────────────────────────
    def _cb_prog(self, done, total):
        self.after(0, lambda: self.progress_bar.set(done / total))
        self.after(0, lambda: self.counter_label.configure(text=f"{done} / {total}"))

    def _cb_log(self, text):
        def _w():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", text)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _w)

    def _cb_fin(self, ok, errors):
        def _d():
            self.btn_convert.configure(state="normal", text="Convert")
            self.status_text.configure(text="Done", text_color=TEXT_GOLD)
            msg = f"Converted:  {ok} file{'s' if ok != 1 else ''}"
            if errors:
                msg += f"\nErrors:  {errors}"
            messagebox.showinfo("Done", msg)
        self.after(0, _d)

    def _log_clear(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _res(self, path):
        try:
            base = sys._MEIPASS
        except Exception:
            base = os.path.abspath(".")
        return os.path.join(base, path)


if __name__ == "__main__":
    app = AteneaDDSApp()
    app.mainloop()
import os
import sys
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageTk


try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_LANCZOS = Image.LANCZOS


FLAG_WIDTH = 1500
FLAG_HEIGHT = 1000
DEFAULT_COLORS = ("#D52B1E", "#FFFFFF", "#0033A0", "#FFD700")

APP_BG = "#EEF2F7"
SURFACE = "#FFFFFF"
SURFACE_MUTED = "#F7F9FC"
BORDER = "#D9E1EC"
TEXT = "#172033"
MUTED = "#667085"
ACCENT = "#2557D6"
ACCENT_HOVER = "#1D46B3"
GOOD = "#177245"
DANGER = "#BA1A1A"

FONT_CHOICES = (
    "Segoe UI",
    "Arial",
    "Verdana",
    "Georgia",
    "Times New Roman",
    "Courier New",
)

FONT_FILES = {
    "Segoe UI": "segoeui.ttf",
    "Arial": "arial.ttf",
    "Verdana": "verdana.ttf",
    "Georgia": "georgia.ttf",
    "Times New Roman": "times.ttf",
    "Courier New": "cour.ttf",
}


def normalize_color(value, fallback="#000000"):
    value = str(value or "").strip()
    try:
        rgb = ImageColor.getrgb(value)
    except ValueError:
        return fallback

    if len(rgb) == 4:
        rgb = rgb[:3]
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def color_to_rgba(value, alpha=1.0, fallback="#000000"):
    color = normalize_color(value, fallback)
    rgb = ImageColor.getrgb(color)
    return rgb[0], rgb[1], rgb[2], int(255 * clamp(alpha, 0.0, 1.0))


def clamp(value, low, high):
    return max(low, min(high, value))


def safe_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError, tk.TclError):
        return default


def safe_int(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError, tk.TclError):
        return default


class ScrollFrame(ttk.Frame):
    def __init__(self, parent, background=APP_BG, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(
            self,
            background=background,
            borderwidth=0,
            highlightthickness=0,
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style="App.TFrame")
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.content.bind("<Configure>", self._sync_scroll_region)
        self.canvas.bind("<Configure>", self._sync_content_width)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _sync_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_content_width(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _bind_mousewheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class FlagDesignerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Flag Designer")
        self.geometry("1280x820")
        self.minsize(980, 680)

        self.current_flag_image = None
        self.preview_photo = None
        self.layers = []
        self.layer_counter = 0
        self._render_after_id = None
        self._preview_after_id = None

        self.base_designs = {
            "Solid field": self.draw_solid_field,
            "Horizontal bicolor": self.draw_horizontal_bicolor,
            "Horizontal tricolor": self.draw_horizontal_tricolor,
            "Vertical tricolor": self.draw_vertical_tricolor,
            "Quartered": self.draw_quartered,
            "Canton on field": self.draw_canton,
            "Nordic cross": self.draw_nordic_cross,
            "Diagonal split": self.draw_diagonal_split,
            "Chevron": self.draw_chevron,
        }
        self.design_hints = {
            "Solid field": "Uses color 1.",
            "Horizontal bicolor": "Uses colors 1 and 2.",
            "Horizontal tricolor": "Uses colors 1, 2, and 3.",
            "Vertical tricolor": "Uses colors 1, 2, and 3.",
            "Quartered": "Uses all four colors.",
            "Canton on field": "Uses color 1 for the canton and color 2 for the field.",
            "Nordic cross": "Uses color 1 for the field, color 2 for the broad cross, and color 3 for the inner cross.",
            "Diagonal split": "Uses colors 1 and 2.",
            "Chevron": "Uses color 1 for the field, color 2 for the chevron, and color 3 for the trim.",
        }
        self.palette_presets = {
            "Classic civic": ("#D52B1E", "#FFFFFF", "#0033A0", "#FFD700"),
            "Clean city": ("#0F3D5E", "#F7F3E8", "#2DAA73", "#E9B44C"),
            "High contrast": ("#111827", "#FFFFFF", "#EF4444", "#F59E0B"),
            "Coastal": ("#005F73", "#E9D8A6", "#0A9396", "#CA6702"),
            "Modern neutral": ("#243B53", "#F4F7FB", "#38A169", "#D69E2E"),
        }

        self.design_var = tk.StringVar(value="Vertical tricolor")
        self.palette_var = tk.StringVar(value="Classic civic")
        self.color_vars = [tk.StringVar(value=color) for color in DEFAULT_COLORS]
        self.status_var = tk.StringVar(value="Ready")
        self.design_hint_var = tk.StringVar(value=self.design_hints[self.design_var.get()])
        self.color_buttons = []

        self.configure(background=APP_BG)
        self.option_add("*Font", ("Segoe UI", 10))
        self.configure_styles()
        self.build_ui()
        self.bind_events()
        self.generate_flag()

    def configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background=APP_BG)
        style.configure("Surface.TFrame", background=SURFACE)
        style.configure("Muted.TFrame", background=SURFACE_MUTED)
        style.configure("Header.TFrame", background=APP_BG)
        style.configure("Preview.TFrame", background=SURFACE)
        style.configure("TLabel", background=SURFACE, foreground=TEXT)
        style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED)
        style.configure("AppMuted.TLabel", background=APP_BG, foreground=MUTED)
        style.configure("Title.TLabel", background=APP_BG, foreground=TEXT, font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", background=APP_BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("SectionTitle.TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI", 11, "bold"))
        style.configure("LayerTitle.TLabel", background=SURFACE_MUTED, foreground=TEXT, font=("Segoe UI", 10, "bold"))
        style.configure("LayerMeta.TLabel", background=SURFACE_MUTED, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        style.configure("Accent.TButton", background=ACCENT, foreground="#FFFFFF", borderwidth=0)
        style.map(
            "Accent.TButton",
            background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)],
            foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")],
        )
        style.configure("Danger.TButton", foreground=DANGER)
        style.configure("Small.TButton", padding=(8, 4), font=("Segoe UI", 9))
        style.configure("TCombobox", padding=(6, 5))
        style.configure("Horizontal.TScale", background=SURFACE)

    def build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.build_header()

        body = ttk.Frame(self, style="App.TFrame", padding=(18, 0, 18, 16))
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, minsize=390, weight=0)
        body.grid_columnconfigure(1, weight=1)

        self.controls = ScrollFrame(body, background=APP_BG)
        self.controls.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        self.build_design_section()
        self.build_layer_section()
        self.build_export_section()

        self.preview_panel = tk.Frame(
            body,
            background=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.preview_panel.grid(row=0, column=1, sticky="nsew")
        self.preview_panel.grid_rowconfigure(1, weight=1)
        self.preview_panel.grid_columnconfigure(0, weight=1)

        preview_header = ttk.Frame(self.preview_panel, style="Surface.TFrame", padding=(16, 14, 16, 8))
        preview_header.grid(row=0, column=0, sticky="ew")
        preview_header.grid_columnconfigure(0, weight=1)
        ttk.Label(preview_header, text="Preview", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            preview_header,
            text="1500 x 1000 px, 3:2 ratio",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.preview_area = tk.Frame(self.preview_panel, background=SURFACE_MUTED)
        self.preview_area.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.preview_area.grid_rowconfigure(0, weight=1)
        self.preview_area.grid_columnconfigure(0, weight=1)
        self.preview_label = tk.Label(self.preview_area, background=SURFACE_MUTED, borderwidth=0)
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        footer = ttk.Frame(self, style="App.TFrame", padding=(18, 0, 18, 12))
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, style="AppMuted.TLabel").grid(row=0, column=0, sticky="w")

    def build_header(self):
        header = ttk.Frame(self, style="Header.TFrame", padding=(18, 16, 18, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_block = ttk.Frame(header, style="Header.TFrame")
        title_block.grid(row=0, column=0, sticky="w")
        ttk.Label(title_block, text="Flag Designer", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_block,
            text="Build a clean flag layout with editable colors, emblems, text, and export-ready output.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        actions = ttk.Frame(header, style="Header.TFrame")
        actions.grid(row=0, column=1, sticky="e")
        ttk.Button(actions, text="Regenerate", command=self.generate_flag).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Save PNG", style="Accent.TButton", command=self.save_flag).grid(row=0, column=1)

    def build_design_section(self):
        section = self.create_section(self.controls.content, "Base design")
        section.grid_columnconfigure(0, weight=1)

        ttk.Label(section, text="Layout", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        design_menu = ttk.Combobox(
            section,
            textvariable=self.design_var,
            values=list(self.base_designs.keys()),
            state="readonly",
        )
        design_menu.grid(row=1, column=0, sticky="ew", pady=(4, 4))
        design_menu.bind("<<ComboboxSelected>>", self.on_design_changed)
        ttk.Label(section, textvariable=self.design_hint_var, style="Muted.TLabel", wraplength=320).grid(
            row=2, column=0, sticky="w", pady=(0, 14)
        )

        palette_row = ttk.Frame(section, style="Surface.TFrame")
        palette_row.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        palette_row.grid_columnconfigure(0, weight=1)
        ttk.Label(palette_row, text="Palette", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        palette_menu = ttk.Combobox(
            palette_row,
            textvariable=self.palette_var,
            values=list(self.palette_presets.keys()),
            state="readonly",
            width=20,
        )
        palette_menu.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Button(palette_row, text="Apply", command=self.apply_palette).grid(row=1, column=1, padx=(8, 0))

        ttk.Separator(section).grid(row=4, column=0, sticky="ew", pady=(2, 12))

        color_wrap = ttk.Frame(section, style="Surface.TFrame")
        color_wrap.grid(row=5, column=0, sticky="ew")
        color_wrap.grid_columnconfigure(1, weight=1)
        for index, color_var in enumerate(self.color_vars):
            label = f"Color {index + 1}"
            self.create_color_row(color_wrap, index, label, color_var)

    def build_layer_section(self):
        self.layer_section = self.create_section(self.controls.content, "Layers")
        self.layer_section.grid_columnconfigure(0, weight=1)

        button_row = ttk.Frame(self.layer_section, style="Surface.TFrame")
        button_row.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)
        ttk.Button(button_row, text="Add emblem", command=self.add_image_layer).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(button_row, text="Add text", command=self.add_text_layer).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.layer_list = ttk.Frame(self.layer_section, style="Surface.TFrame")
        self.layer_list.grid(row=1, column=0, sticky="ew")
        self.layer_list.grid_columnconfigure(0, weight=1)
        self.refresh_layer_panel()

    def build_export_section(self):
        section = self.create_section(self.controls.content, "Export")
        section.grid_columnconfigure(0, weight=1)
        ttk.Label(
            section,
            text="Exports are saved at full resolution with transparent layer compositing flattened into the flag.",
            style="Muted.TLabel",
            wraplength=320,
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))
        ttk.Button(section, text="Save as PNG", style="Accent.TButton", command=self.save_flag).grid(row=1, column=0, sticky="ew")
        ttk.Button(section, text="Clear all layers", command=self.clear_layers).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def bind_events(self):
        for index, color_var in enumerate(self.color_vars):
            color_var.trace_add("write", lambda *_args, index=index: self.on_color_changed(index))
        self.preview_area.bind("<Configure>", self.schedule_preview_update)

    def create_section(self, parent, title):
        outer = tk.Frame(
            parent,
            background=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        outer.pack(fill="x", padx=0, pady=(0, 14))

        frame = ttk.Frame(outer, style="Surface.TFrame", padding=16)
        frame.pack(fill="x", expand=True)
        ttk.Label(frame, text=title, style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
        content = ttk.Frame(frame, style="Surface.TFrame")
        content.grid(row=1, column=0, sticky="ew")
        content.grid_columnconfigure(0, weight=1)
        return content

    def create_color_row(self, parent, index, label, variable):
        row = ttk.Frame(parent, style="Surface.TFrame")
        row.grid(row=index, column=0, sticky="ew", pady=(0, 8))
        row.grid_columnconfigure(1, weight=1)

        ttk.Label(row, text=label, style="Muted.TLabel", width=10).grid(row=0, column=0, sticky="w", padx=(0, 8))
        entry = ttk.Entry(row, textvariable=variable)
        entry.grid(row=0, column=1, sticky="ew")

        swatch = tk.Button(
            row,
            text="",
            width=4,
            command=lambda i=index: self.choose_base_color(i),
            background=normalize_color(variable.get(), DEFAULT_COLORS[index]),
            activebackground=normalize_color(variable.get(), DEFAULT_COLORS[index]),
            borderwidth=1,
            relief="solid",
            highlightthickness=0,
        )
        swatch.grid(row=0, column=2, sticky="e", padx=(8, 0), ipady=4)
        self.color_buttons.append(swatch)

    def create_layer_color_control(self, parent, label, variable):
        row = ttk.Frame(parent, style="Muted.TFrame")
        row.grid_columnconfigure(1, weight=1)
        ttk.Label(row, text=label, style="LayerMeta.TLabel", width=11).grid(row=0, column=0, sticky="w", padx=(0, 8))
        entry = ttk.Entry(row, textvariable=variable)
        entry.grid(row=0, column=1, sticky="ew")
        swatch = tk.Button(
            row,
            text="",
            width=4,
            background=normalize_color(variable.get()),
            activebackground=normalize_color(variable.get()),
            borderwidth=1,
            relief="solid",
            highlightthickness=0,
            command=lambda: self.choose_layer_color(variable, swatch),
        )
        swatch.grid(row=0, column=2, padx=(8, 0), ipady=4)
        entry.bind("<FocusOut>", lambda _event: self.update_single_swatch(swatch, variable.get()))
        return row

    def on_design_changed(self, _event=None):
        design = self.design_var.get()
        self.design_hint_var.set(self.design_hints.get(design, ""))
        self.schedule_render()

    def on_color_changed(self, index):
        self.update_color_swatch(index)
        self.schedule_render()

    def update_color_swatch(self, index):
        if index >= len(self.color_buttons):
            return
        color = normalize_color(self.color_vars[index].get(), DEFAULT_COLORS[index])
        self.color_buttons[index].configure(background=color, activebackground=color)

    def update_single_swatch(self, swatch, value):
        color = normalize_color(value)
        swatch.configure(background=color, activebackground=color)

    def choose_base_color(self, index):
        current = normalize_color(self.color_vars[index].get(), DEFAULT_COLORS[index])
        chosen = colorchooser.askcolor(color=current, title=f"Choose color {index + 1}")
        if chosen and chosen[1]:
            self.color_vars[index].set(chosen[1].upper())

    def choose_layer_color(self, variable, swatch):
        current = normalize_color(variable.get())
        chosen = colorchooser.askcolor(color=current, title="Choose layer color")
        if chosen and chosen[1]:
            variable.set(chosen[1].upper())
            self.update_single_swatch(swatch, variable.get())

    def apply_palette(self):
        colors = self.palette_presets.get(self.palette_var.get(), DEFAULT_COLORS)
        for color_var, color in zip(self.color_vars, colors):
            color_var.set(color)
        self.status_var.set(f"Applied {self.palette_var.get()} palette.")
        self.generate_flag()

    def add_image_layer(self):
        path = filedialog.askopenfilename(
            title="Choose emblem image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            image = Image.open(path).convert("RGBA")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not add image", f"The selected file could not be opened.\n\n{exc}")
            return

        layer = {
            "id": self.next_layer_id(),
            "type": "image",
            "name": os.path.basename(path),
            "path": path,
            "image": image,
            "pos_x_var": tk.DoubleVar(value=0),
            "pos_y_var": tk.DoubleVar(value=0),
            "scale_var": tk.DoubleVar(value=0.35),
            "opacity_var": tk.DoubleVar(value=1.0),
        }
        self.trace_layer_vars(layer, ("pos_x_var", "pos_y_var", "scale_var", "opacity_var"))
        self.layers.append(layer)
        self.refresh_layer_panel()
        self.generate_flag()
        self.status_var.set(f"Added emblem layer: {layer['name']}")

    def add_text_layer(self):
        layer = {
            "id": self.next_layer_id(),
            "type": "text",
            "name": "Text",
            "text_var": tk.StringVar(value="Your Text"),
            "font_var": tk.StringVar(value="Segoe UI"),
            "fill_var": tk.StringVar(value="#FFFFFF"),
            "outline_var": tk.StringVar(value="#111827"),
            "outline_width_var": tk.IntVar(value=4),
            "pos_x_var": tk.DoubleVar(value=0),
            "pos_y_var": tk.DoubleVar(value=0),
            "scale_var": tk.DoubleVar(value=1.0),
            "opacity_var": tk.DoubleVar(value=1.0),
        }
        self.trace_layer_vars(
            layer,
            (
                "text_var",
                "font_var",
                "fill_var",
                "outline_var",
                "outline_width_var",
                "pos_x_var",
                "pos_y_var",
                "scale_var",
                "opacity_var",
            ),
        )
        self.layers.append(layer)
        self.refresh_layer_panel()
        self.generate_flag()
        self.status_var.set("Added text layer.")

    def next_layer_id(self):
        self.layer_counter += 1
        return self.layer_counter

    def trace_layer_vars(self, layer, keys):
        for key in keys:
            layer[key].trace_add("write", self.schedule_render)

    def refresh_layer_panel(self):
        for child in self.layer_list.winfo_children():
            child.destroy()

        if not self.layers:
            empty = ttk.Label(
                self.layer_list,
                text="No layers yet. Add text or an emblem to start composing.",
                style="Muted.TLabel",
                wraplength=320,
            )
            empty.grid(row=0, column=0, sticky="ew", pady=(2, 0))
            return

        for index, layer in enumerate(reversed(self.layers)):
            real_index = len(self.layers) - 1 - index
            card = tk.Frame(
                self.layer_list,
                background=SURFACE_MUTED,
                highlightbackground=BORDER,
                highlightthickness=1,
            )
            card.grid(row=index, column=0, sticky="ew", pady=(0, 10))
            card.grid_columnconfigure(0, weight=1)

            content = ttk.Frame(card, style="Muted.TFrame", padding=12)
            content.grid(row=0, column=0, sticky="ew")
            content.grid_columnconfigure(0, weight=1)

            self.build_layer_card(content, layer, real_index)

    def build_layer_card(self, parent, layer, index):
        header = ttk.Frame(parent, style="Muted.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = layer["name"] if layer["type"] == "image" else "Text layer"
        ttk.Label(header, text=title, style="LayerTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text=f"{layer['type'].title()} layer {index + 1}",
            style="LayerMeta.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        actions = ttk.Frame(header, style="Muted.TFrame")
        actions.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Button(actions, text="Back", style="Small.TButton", command=lambda: self.move_layer(index, -1)).grid(
            row=0,
            column=0,
            padx=(0, 4),
        )
        ttk.Button(actions, text="Forward", style="Small.TButton", command=lambda: self.move_layer(index, 1)).grid(
            row=0,
            column=1,
            padx=(0, 4),
        )
        ttk.Button(actions, text="Delete", style="Small.TButton", command=lambda: self.remove_layer(layer)).grid(row=0, column=2)

        ttk.Separator(parent).grid(row=1, column=0, sticky="ew", pady=10)

        row = 2
        if layer["type"] == "text":
            ttk.Label(parent, text="Text", style="LayerMeta.TLabel").grid(row=row, column=0, sticky="w")
            ttk.Entry(parent, textvariable=layer["text_var"]).grid(row=row + 1, column=0, sticky="ew", pady=(3, 8))
            row += 2

            ttk.Label(parent, text="Font", style="LayerMeta.TLabel").grid(row=row, column=0, sticky="w")
            font_menu = ttk.Combobox(
                parent,
                textvariable=layer["font_var"],
                values=FONT_CHOICES,
                state="readonly",
            )
            font_menu.grid(row=row + 1, column=0, sticky="ew", pady=(3, 8))
            row += 2

            fill_row = self.create_layer_color_control(parent, "Fill", layer["fill_var"])
            fill_row.grid(row=row, column=0, sticky="ew", pady=(0, 8))
            row += 1

            outline_row = self.create_layer_color_control(parent, "Outline", layer["outline_var"])
            outline_row.grid(row=row, column=0, sticky="ew", pady=(0, 8))
            row += 1

            outline_frame = ttk.Frame(parent, style="Muted.TFrame")
            outline_frame.grid(row=row, column=0, sticky="ew", pady=(0, 8))
            outline_frame.grid_columnconfigure(1, weight=1)
            ttk.Label(outline_frame, text="Outline px", style="LayerMeta.TLabel", width=11).grid(
                row=0, column=0, sticky="w", padx=(0, 8)
            )
            ttk.Spinbox(
                outline_frame,
                from_=0,
                to=24,
                increment=1,
                textvariable=layer["outline_width_var"],
                width=8,
                command=self.schedule_render,
            ).grid(row=0, column=1, sticky="w")
            row += 1

        self.add_scale_control(parent, row, "Position X", layer["pos_x_var"], -FLAG_WIDTH // 2, FLAG_WIDTH // 2, "{:.0f}px")
        row += 1
        self.add_scale_control(parent, row, "Position Y", layer["pos_y_var"], -FLAG_HEIGHT // 2, FLAG_HEIGHT // 2, "{:.0f}px")
        row += 1
        self.add_scale_control(parent, row, "Scale", layer["scale_var"], 0.1, 3.0, "{:.2f}x")
        row += 1
        self.add_scale_control(parent, row, "Opacity", layer["opacity_var"], 0.0, 1.0, "{:.0%}")

    def add_scale_control(self, parent, row_index, label, variable, low, high, fmt):
        frame = ttk.Frame(parent, style="Muted.TFrame")
        frame.grid(row=row_index, column=0, sticky="ew", pady=(0, 8))
        frame.grid_columnconfigure(0, weight=1)

        value_label = ttk.Label(frame, text=fmt.format(safe_float(variable.get(), low)), style="LayerMeta.TLabel")
        ttk.Label(frame, text=label, style="LayerMeta.TLabel").grid(row=0, column=0, sticky="w")
        value_label.grid(row=0, column=1, sticky="e")
        ttk.Scale(
            frame,
            from_=low,
            to=high,
            variable=variable,
            command=lambda value: value_label.configure(text=fmt.format(float(value))),
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    def move_layer(self, index, direction):
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.layers):
            return
        self.layers[index], self.layers[new_index] = self.layers[new_index], self.layers[index]
        self.refresh_layer_panel()
        self.generate_flag()

    def remove_layer(self, layer):
        if layer in self.layers:
            self.layers.remove(layer)
            self.refresh_layer_panel()
            self.generate_flag()
            self.status_var.set("Layer removed.")

    def clear_layers(self):
        if not self.layers:
            self.status_var.set("There are no layers to clear.")
            return
        if not messagebox.askyesno("Clear layers", "Remove every text and emblem layer?"):
            return
        self.layers.clear()
        self.refresh_layer_panel()
        self.generate_flag()
        self.status_var.set("All layers cleared.")

    def schedule_render(self, *_args):
        if self._render_after_id is not None:
            try:
                self.after_cancel(self._render_after_id)
            except tk.TclError:
                pass
        self._render_after_id = self.after(45, self.generate_flag)

    def schedule_preview_update(self, _event=None):
        if self._preview_after_id is not None:
            try:
                self.after_cancel(self._preview_after_id)
            except tk.TclError:
                pass
        self._preview_after_id = self.after(80, self.update_preview)

    def generate_flag(self, *_args):
        if self._render_after_id is not None:
            try:
                self.after_cancel(self._render_after_id)
            except tk.TclError:
                pass
            self._render_after_id = None

        colors = [
            normalize_color(color_var.get(), DEFAULT_COLORS[index])
            for index, color_var in enumerate(self.color_vars)
        ]

        image = Image.new("RGBA", (FLAG_WIDTH, FLAG_HEIGHT), colors[0])
        draw = ImageDraw.Draw(image)
        design = self.design_var.get()
        draw_base = self.base_designs.get(design, self.draw_vertical_tricolor)
        draw_base(draw, FLAG_WIDTH, FLAG_HEIGHT, colors)

        self.current_flag_image = image
        for layer in self.layers:
            if layer["type"] == "image":
                self.draw_image_layer(layer)
            elif layer["type"] == "text":
                self.draw_text_layer(layer)

        self.update_preview()
        self.status_var.set(f"Preview updated. {len(self.layers)} layer(s).")

    def update_preview(self):
        if self.current_flag_image is None:
            return

        if self._preview_after_id is not None:
            self._preview_after_id = None

        area_w = max(320, self.preview_area.winfo_width())
        area_h = max(260, self.preview_area.winfo_height())
        max_w = max(260, area_w - 64)
        max_h = max(180, area_h - 64)
        preview = self.current_flag_image.convert("RGB").copy()
        preview.thumbnail((max_w, max_h), RESAMPLE_LANCZOS)

        pad = 22
        shadow_offset = 8
        canvas_w = preview.width + pad * 2 + shadow_offset
        canvas_h = preview.height + pad * 2 + shadow_offset
        canvas = Image.new("RGB", (canvas_w, canvas_h), SURFACE_MUTED)
        draw = ImageDraw.Draw(canvas)
        shadow_box = [pad + shadow_offset, pad + shadow_offset, pad + shadow_offset + preview.width, pad + shadow_offset + preview.height]
        flag_box = [pad, pad, pad + preview.width, pad + preview.height]
        draw.rounded_rectangle(shadow_box, radius=12, fill="#D6DEEA")
        draw.rounded_rectangle(flag_box, radius=10, fill=SURFACE, outline=BORDER, width=1)
        canvas.paste(preview, (pad, pad))
        draw.rectangle(flag_box, outline="#C8D2DF", width=1)

        self.preview_photo = ImageTk.PhotoImage(canvas)
        self.preview_label.configure(image=self.preview_photo)

    def draw_image_layer(self, layer):
        source = layer.get("image")
        if source is None:
            return

        scale = clamp(safe_float(layer["scale_var"].get(), 1.0), 0.05, 4.0)
        opacity = clamp(safe_float(layer["opacity_var"].get(), 1.0), 0.0, 1.0)
        width = max(1, int(source.width * scale))
        height = max(1, int(source.height * scale))

        overlay = source.resize((width, height), RESAMPLE_LANCZOS)
        if opacity < 1.0:
            alpha = overlay.getchannel("A").point(lambda pixel: int(pixel * opacity))
            overlay.putalpha(alpha)

        pos_x = int((FLAG_WIDTH - overlay.width) / 2 + safe_float(layer["pos_x_var"].get(), 0))
        pos_y = int((FLAG_HEIGHT - overlay.height) / 2 + safe_float(layer["pos_y_var"].get(), 0))
        self.current_flag_image.alpha_composite(overlay, (pos_x, pos_y))

    def draw_text_layer(self, layer):
        text = layer["text_var"].get()
        if not text.strip():
            return

        scale = clamp(safe_float(layer["scale_var"].get(), 1.0), 0.1, 3.0)
        opacity = clamp(safe_float(layer["opacity_var"].get(), 1.0), 0.0, 1.0)
        font_size = max(8, int(86 * scale))
        stroke_width = clamp(safe_int(layer["outline_width_var"].get(), 4), 0, 24)
        font = self.load_font(layer["font_var"].get(), font_size)

        fill = color_to_rgba(layer["fill_var"].get(), opacity, "#FFFFFF")
        outline = color_to_rgba(layer["outline_var"].get(), opacity, "#111827")

        text_layer = Image.new("RGBA", (FLAG_WIDTH, FLAG_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        spacing = max(4, int(font_size * 0.18))

        bbox = draw.multiline_textbbox(
            (0, 0),
            text,
            font=font,
            spacing=spacing,
            stroke_width=stroke_width,
            align="center",
        )
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        pos_x = (FLAG_WIDTH - text_width) / 2 + safe_float(layer["pos_x_var"].get(), 0) - bbox[0]
        pos_y = (FLAG_HEIGHT - text_height) / 2 + safe_float(layer["pos_y_var"].get(), 0) - bbox[1]

        draw.multiline_text(
            (pos_x, pos_y),
            text,
            font=font,
            fill=fill,
            spacing=spacing,
            align="center",
            stroke_width=stroke_width,
            stroke_fill=outline,
        )
        self.current_flag_image.alpha_composite(text_layer)

    def load_font(self, font_name, size):
        candidates = []
        file_name = FONT_FILES.get(font_name, font_name)
        candidates.append(file_name)

        if sys.platform.startswith("win"):
            windir = os.environ.get("WINDIR", r"C:\Windows")
            candidates.append(os.path.join(windir, "Fonts", file_name))

        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue

        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    def save_flag(self):
        self.generate_flag()
        if self.current_flag_image is None:
            messagebox.showwarning("Nothing to save", "Generate a flag before saving.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Save flag as PNG",
            defaultextension=".png",
            initialfile="flag-design.png",
            filetypes=[("PNG image", "*.png")],
        )
        if not filepath:
            return

        try:
            self.current_flag_image.convert("RGB").save(filepath, "PNG")
        except OSError as exc:
            messagebox.showerror("Save failed", f"The flag could not be saved.\n\n{exc}")
            return

        self.status_var.set(f"Saved {os.path.basename(filepath)}")
        messagebox.showinfo("Flag saved", f"Saved full-resolution PNG:\n{filepath}")

    def draw_solid_field(self, draw, w, h, colors):
        draw.rectangle([0, 0, w, h], fill=colors[0])

    def draw_horizontal_bicolor(self, draw, w, h, colors):
        draw.rectangle([0, 0, w, h // 2], fill=colors[0])
        draw.rectangle([0, h // 2, w, h], fill=colors[1])

    def draw_horizontal_tricolor(self, draw, w, h, colors):
        stripe_h = h / 3
        for index in range(3):
            draw.rectangle([0, int(index * stripe_h), w, int((index + 1) * stripe_h)], fill=colors[index])

    def draw_vertical_tricolor(self, draw, w, h, colors):
        stripe_w = w / 3
        for index in range(3):
            draw.rectangle([int(index * stripe_w), 0, int((index + 1) * stripe_w), h], fill=colors[index])

    def draw_quartered(self, draw, w, h, colors):
        draw.rectangle([0, 0, w // 2, h // 2], fill=colors[0])
        draw.rectangle([w // 2, 0, w, h // 2], fill=colors[1])
        draw.rectangle([0, h // 2, w // 2, h], fill=colors[2])
        draw.rectangle([w // 2, h // 2, w, h], fill=colors[3])

    def draw_canton(self, draw, w, h, colors):
        draw.rectangle([0, 0, w, h], fill=colors[1])
        draw.rectangle([0, 0, int(w * 0.48), int(h * 0.52)], fill=colors[0])

    def draw_nordic_cross(self, draw, w, h, colors):
        draw.rectangle([0, 0, w, h], fill=colors[0])
        broad = int(h * 0.22)
        narrow = int(h * 0.11)
        x_center = int(w * 0.38)
        y_center = h // 2
        draw.rectangle([x_center - broad // 2, 0, x_center + broad // 2, h], fill=colors[1])
        draw.rectangle([0, y_center - broad // 2, w, y_center + broad // 2], fill=colors[1])
        draw.rectangle([x_center - narrow // 2, 0, x_center + narrow // 2, h], fill=colors[2])
        draw.rectangle([0, y_center - narrow // 2, w, y_center + narrow // 2], fill=colors[2])

    def draw_diagonal_split(self, draw, w, h, colors):
        draw.rectangle([0, 0, w, h], fill=colors[1])
        draw.polygon([(0, 0), (w, 0), (0, h)], fill=colors[0])

    def draw_chevron(self, draw, w, h, colors):
        draw.rectangle([0, 0, w, h], fill=colors[0])
        draw.polygon([(0, 0), (int(w * 0.46), h // 2), (0, h)], fill=colors[2])
        draw.polygon([(0, int(h * 0.08)), (int(w * 0.36), h // 2), (0, int(h * 0.92))], fill=colors[1])


if __name__ == "__main__":
    app = FlagDesignerApp()
    app.mainloop()

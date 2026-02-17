import tkinter
import customtkinter
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk

# --- Main Application Class ---
class AdvancedFlagDesignerApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Flag Designer")
        self.geometry("1200x800")

        # --- Constants & State ---
        self.FLAG_WIDTH = 1500  # Higher resolution for better quality
        self.FLAG_HEIGHT = 1000
        self.current_flag_image = None
        self.layers = [] # This will hold all our image and text layers
        self.fonts = ["Arial", "Courier New", "Times New Roman", "Verdana", "Georgia"]
        self.base_designs = {
            "Solid Color": self.draw_solid_color,
            "Vertical Tricolor": self.draw_vertical_tricolor,
            "Horizontal Bicolor": self.draw_horizontal_bicolor,
            "Quartered (2x2)": self.draw_quartered,
            "With Canton": self.draw_with_canton,
        }

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=2)  # Control Panel
        self.grid_columnconfigure(1, weight=5)  # Preview Panel
        self.grid_rowconfigure(0, weight=1)

        # --- Left: Control Panel ---
        self.controls_frame = customtkinter.CTkFrame(self)
        self.controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")
        self.create_base_controls()

        # --- Right: Preview Panel ---
        self.preview_frame = customtkinter.CTkFrame(self)
        self.preview_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nswe")
        self.preview_label = customtkinter.CTkLabel(self.preview_frame, text="")
        self.preview_label.pack(expand=True)

        self.generate_flag()

    def create_base_controls(self):
        """Creates the base design and layer management controls."""
        # --- Base Design Controls ---
        base_frame = customtkinter.CTkFrame(self.controls_frame)
        base_frame.pack(pady=10, padx=10, fill="x")
        customtkinter.CTkLabel(base_frame, text="Base Design", font=customtkinter.CTkFont(weight="bold")).pack()
        
        self.design_menu = customtkinter.CTkOptionMenu(base_frame, values=list(self.base_designs.keys()), command=self.generate_flag)
        self.design_menu.pack(padx=10, pady=5, fill="x")

        # Color Inputs
        self.color_entries = []
        for i in range(4): # For up to 4 colors in quartered design
            entry = customtkinter.CTkEntry(base_frame, placeholder_text=f"Color {i+1} (e.g., #FFFFFF)")
            entry.pack(padx=10, pady=2, fill="x")
            self.color_entries.append(entry)
        self.color_entries[0].insert(0, "#D52B1E") # Red
        self.color_entries[1].insert(0, "#FFFFFF") # White
        self.color_entries[2].insert(0, "#0033A0") # Blue
        self.color_entries[3].insert(0, "#FFD700") # Gold

        # --- Layer Management ---
        layer_mgmt_frame = customtkinter.CTkFrame(self.controls_frame)
        layer_mgmt_frame.pack(pady=10, padx=10, fill="x")
        customtkinter.CTkLabel(layer_mgmt_frame, text="Layers", font=customtkinter.CTkFont(weight="bold")).pack()

        add_buttons_frame = customtkinter.CTkFrame(layer_mgmt_frame)
        add_buttons_frame.pack(fill="x", pady=5)
        customtkinter.CTkButton(add_buttons_frame, text="Add Image/Emblem", command=self.add_image_layer).pack(side="left", expand=True, padx=5)
        customtkinter.CTkButton(add_buttons_frame, text="Add Text", command=self.add_text_layer).pack(side="right", expand=True, padx=5)
        
        # --- Scrollable frame for layer controls ---
        self.layer_panel = customtkinter.CTkScrollableFrame(self.controls_frame, label_text="Layer Controls")
        self.layer_panel.pack(pady=10, padx=10, fill="both", expand=True)
        
        # --- Final Buttons ---
        final_buttons_frame = customtkinter.CTkFrame(self.controls_frame)
        final_buttons_frame.pack(pady=10, padx=10, fill="x", side="bottom")
        customtkinter.CTkButton(final_buttons_frame, text="Generate Flag", command=self.generate_flag, height=40).pack(fill="x")
        customtkinter.CTkButton(final_buttons_frame, text="Save as PNG", command=self.save_flag).pack(fill="x", pady=5)


    def add_layer_controls(self, layer_type, layer_data):
        """Adds a new set of controls for a layer to the layer panel."""
        layer_frame = customtkinter.CTkFrame(self.layer_panel)
        layer_frame.pack(pady=5, padx=5, fill="x")
        
        # Add a remove button to every layer
        customtkinter.CTkButton(layer_frame, text="X", width=25, fg_color="red", command=lambda l=layer_frame, d=layer_data: self.remove_layer(l, d)).pack(side="right")
        
        if layer_type == "image":
            customtkinter.CTkLabel(layer_frame, text=f"Image: {os.path.basename(layer_data['path'])}").pack(anchor="w")
            
        if layer_type == "text":
            customtkinter.CTkLabel(layer_frame, text="Text Layer").pack(anchor="w")
            entry = customtkinter.CTkEntry(layer_frame, textvariable=layer_data['text_var'])
            entry.pack(fill="x", padx=5, pady=2)
            customtkinter.CTkOptionMenu(layer_frame, variable=layer_data['font_var'], values=self.fonts).pack(fill="x", padx=5, pady=2)

        # Common controls for position and scale
        customtkinter.CTkLabel(layer_frame, text="Position X:").pack(anchor="w", padx=5)
        customtkinter.CTkSlider(layer_frame, from_=-self.FLAG_WIDTH//2, to=self.FLAG_WIDTH//2, variable=layer_data['pos_x_var']).pack(fill="x", padx=5)
        
        customtkinter.CTkLabel(layer_frame, text="Position Y:").pack(anchor="w", padx=5)
        customtkinter.CTkSlider(layer_frame, from_=-self.FLAG_HEIGHT//2, to=self.FLAG_HEIGHT//2, variable=layer_data['pos_y_var']).pack(fill="x", padx=5)
        
        customtkinter.CTkLabel(layer_frame, text="Scale:").pack(anchor="w", padx=5)
        customtkinter.CTkSlider(layer_frame, from_=0.1, to=3.0, variable=layer_data['scale_var']).pack(fill="x", padx=5)


    def add_image_layer(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if not path: return
        
        layer_data = {
            "type": "image", "path": path,
            "pos_x_var": customtkinter.DoubleVar(value=0), "pos_y_var": customtkinter.DoubleVar(value=0),
            "scale_var": customtkinter.DoubleVar(value=1.0)
        }
        # Add a listener to regenerate flag when sliders move
        for var in [layer_data['pos_x_var'], layer_data['pos_y_var'], layer_data['scale_var']]:
            var.trace_add("write", self.generate_flag)
            
        self.layers.append(layer_data)
        self.add_layer_controls("image", layer_data)
        self.generate_flag()

    def add_text_layer(self):
        layer_data = {
            "type": "text",
            "text_var": customtkinter.StringVar(value="Your Text"), "font_var": customtkinter.StringVar(value="Arial"),
            "pos_x_var": customtkinter.DoubleVar(value=0), "pos_y_var": customtkinter.DoubleVar(value=0),
            "scale_var": customtkinter.DoubleVar(value=1.0) # Scale will affect font size
        }
        for var in [layer_data['text_var'], layer_data['font_var'], layer_data['pos_x_var'], layer_data['pos_y_var'], layer_data['scale_var']]:
            var.trace_add("write", self.generate_flag)
            
        self.layers.append(layer_data)
        self.add_layer_controls("text", layer_data)
        self.generate_flag()

    def remove_layer(self, layer_frame, layer_data):
        self.layers.remove(layer_data)
        layer_frame.destroy()
        self.generate_flag()

    def generate_flag(self, *args):
        # 1. Draw Base Design
        base_design_name = self.design_menu.get()
        colors = [entry.get() for entry in self.color_entries]
        
        self.current_flag_image = Image.new("RGBA", (self.FLAG_WIDTH, self.FLAG_HEIGHT), (0,0,0,0))
        draw = ImageDraw.Draw(self.current_flag_image)
        self.base_designs[base_design_name](draw, self.FLAG_WIDTH, self.FLAG_HEIGHT, colors)

        # 2. Draw all layers on top
        for layer in self.layers:
            if layer['type'] == 'image':
                self.draw_image_layer(layer)
            elif layer['type'] == 'text':
                self.draw_text_layer(draw, layer)

        # 3. Update Preview
        # Use a high-quality downscaling filter
        display_img = self.current_flag_image.resize((int(self.FLAG_WIDTH*0.4), int(self.FLAG_HEIGHT*0.4)), Image.LANCZOS)
        ctk_image = customtkinter.CTkImage(light_image=display_img, size=display_img.size)
        self.preview_label.configure(image=ctk_image)
        
    def draw_image_layer(self, layer):
        try:
            overlay_img = Image.open(layer['path']).convert("RGBA")
            scale = layer['scale_var'].get()
            new_size = (int(overlay_img.width * scale), int(overlay_img.height * scale))
            overlay_img = overlay_img.resize(new_size, Image.LANCZOS)
            
            # Position relative to center
            center_x, center_y = self.FLAG_WIDTH / 2, self.FLAG_HEIGHT / 2
            pos_x = int(center_x + layer['pos_x_var'].get() - overlay_img.width / 2)
            pos_y = int(center_y + layer['pos_y_var'].get() - overlay_img.height / 2)
            
            # Paste image using its own alpha channel as a mask
            self.current_flag_image.paste(overlay_img, (pos_x, pos_y), overlay_img)
        except Exception as e:
            print(f"Could not load image {layer['path']}: {e}")

    def draw_text_layer(self, draw, layer):
        text = layer['text_var'].get()
        if not text: return

        font_name = layer['font_var'].get()
        scale = layer['scale_var'].get()
        font_size = int(80 * scale)

        try:
            font = ImageFont.truetype(f"{font_name.lower()}bd.ttf", size=font_size)
        except IOError:
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        
        center_x, center_y = self.FLAG_WIDTH / 2, self.FLAG_HEIGHT / 2
        pos_x = center_x + layer['pos_x_var'].get() - text_width / 2
        pos_y = center_y + layer['pos_y_var'].get() - text_height / 2
        
        draw.text((pos_x, pos_y), text, font=font, fill="white", stroke_width=2, stroke_fill="black")

    def save_flag(self):
        if self.current_flag_image:
            filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
            if filepath:
                self.current_flag_image.save(filepath)

    # --- BASE DESIGN FUNCTIONS ---
    def draw_solid_color(self, draw, w, h, c): draw.rectangle([0, 0, w, h], fill=c[0])
    def draw_horizontal_bicolor(self, draw, w, h, c):
        draw.rectangle([0, 0, w, h/2], fill=c[0]); draw.rectangle([0, h/2, w, h], fill=c[1])
    def draw_vertical_tricolor(self, draw, w, h, c):
        draw.rectangle([0, 0, w/3, h], fill=c[0]); draw.rectangle([w/3, 0, 2*w/3, h], fill=c[1]); draw.rectangle([2*w/3, 0, w, h], fill=c[2])
    def draw_quartered(self, draw, w, h, c):
        draw.rectangle([0, 0, w/2, h/2], fill=c[0]); draw.rectangle([w/2, 0, w, h/2], fill=c[1])
        draw.rectangle([0, h/2, w/2, h], fill=c[2]); draw.rectangle([w/2, h/2, w, h], fill=c[3])
    def draw_with_canton(self, draw, w, h, c):
        draw.rectangle([0, 0, w, h], fill=c[1]); draw.rectangle([0, 0, w/2, h/2], fill=c[0])

if __name__ == "__main__":
    customtkinter.set_appearance_mode("Dark")
    app = AdvancedFlagDesignerApp()
    app.mainloop()
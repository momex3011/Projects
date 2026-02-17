import tkinter
import customtkinter
from tkinter import filedialog
import os
import shutil
import time
import threading

# --- Main Application Class ---
class DesktopOrganizerApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Smart Desktop Organizer")
        self.geometry("700x550")

        # --- State Variables ---
        self.source_folder = ""
        self.is_running = False
        self.sorting_thread = None

        # --- Define Sorting Rules ---
        # You can easily add more extensions or categories here
        self.rules = {
            "Images": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"),
            "Documents": (".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".csv"),
            "Videos": (".mp4", ".mov", ".avi", ".mkv", ".flv"),
            "Audio": (".mp3", ".wav", ".aac", ".flac"),
            "Archives": (".zip", ".rar", ".tar", ".gz", ".7z"),
            "Scripts": (".py", ".js", ".html", ".css", ".sh"),
        }

        # --- Main Frame ---
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # --- Title Label ---
        self.title_label = customtkinter.CTkLabel(self.main_frame, text="Smart Desktop Organizer", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=10)

        # --- Folder Selection Section ---
        self.source_frame = customtkinter.CTkFrame(self.main_frame)
        self.source_frame.pack(pady=10, fill="x", padx=10)

        self.source_path_label = customtkinter.CTkLabel(self.source_frame, text="Select a folder to organize...")
        self.source_path_label.pack(side="left", padx=10)

        self.select_source_button = customtkinter.CTkButton(self.source_frame, text="Browse Folder", command=self.select_source_folder)
        self.select_source_button.pack(side="right", padx=10)

        # --- Control Buttons Section ---
        self.control_frame = customtkinter.CTkFrame(self.main_frame)
        self.control_frame.pack(pady=10)

        self.start_button = customtkinter.CTkButton(self.control_frame, text="Start Organizing", command=self.start_sorting, fg_color="green")
        self.start_button.pack(side="left", padx=10)

        self.stop_button = customtkinter.CTkButton(self.control_frame, text="Stop Organizing", command=self.stop_sorting, fg_color="red", state="disabled")
        self.stop_button.pack(side="left", padx=10)

        # --- Live Log Section ---
        self.log_label = customtkinter.CTkLabel(self.main_frame, text="Activity Log:")
        self.log_label.pack(pady=(10, 0))

        self.output_textbox = customtkinter.CTkTextbox(self.main_frame, width=600, height=200, wrap="word")
        self.output_textbox.pack(pady=10, padx=10, fill="both", expand=True)
        
        # --- Handle closing the window ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def select_source_folder(self):
        """Opens a dialog to select the folder to be organized."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_folder = folder_selected
            # Truncate path if it's too long to display nicely
            display_path = self.source_folder
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]
            self.source_path_label.configure(text=f"Monitoring: {display_path}")
            self.log_message(f"Selected folder: {self.source_folder}")

    def log_message(self, message):
        """Adds a message to the log box with a timestamp and scrolls to the end."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.output_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.output_textbox.see("end")
        self.update_idletasks()

    def start_sorting(self):
        """Starts the file sorting process in a background thread."""
        if not self.source_folder:
            self.log_message("ERROR: Please select a source folder first.")
            return
        
        if self.is_running:
            self.log_message("INFO: Organizer is already running.")
            return

        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.select_source_button.configure(state="disabled")
        self.log_message("Organizer started. Watching for new files...")

        # Run the sorting process in a daemon thread
        self.sorting_thread = threading.Thread(target=self.sorting_process, daemon=True)
        self.sorting_thread.start()

    def stop_sorting(self):
        """Stops the file sorting process."""
        if not self.is_running:
            self.log_message("INFO: Organizer is not running.")
            return

        self.is_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.select_source_button.configure(state="normal")
        self.log_message("Organizer stopped.")

    def sorting_process(self):
        """The core logic that watches and sorts files."""
        while self.is_running:
            try:
                for filename in os.listdir(self.source_folder):
                    file_path = os.path.join(self.source_folder, filename)
                    
                    # Skip if it's a directory or not a file
                    if not os.path.isfile(file_path):
                        continue
                    
                    # Get file extension
                    _, extension = os.path.splitext(filename)
                    extension = extension.lower()

                    # Find the correct category for the file
                    moved = False
                    for category, extensions in self.rules.items():
                        if extension in extensions:
                            dest_dir = os.path.join(self.source_folder, category)
                            # Create the category folder if it doesn't exist
                            os.makedirs(dest_dir, exist_ok=True)
                            
                            dest_path = os.path.join(dest_dir, filename)
                            shutil.move(file_path, dest_path)
                            self.log_message(f"Moved: {filename} -> {category}")
                            moved = True
                            break
                    
            except Exception as e:
                self.log_message(f"ERROR: An error occurred - {e}")
            
            # Wait for 5 seconds before checking again
            time.sleep(5)

    def on_closing(self):
        """Handles what happens when the user closes the window."""
        if self.is_running:
            self.stop_sorting()
        self.destroy()

# --- Main execution block ---
if __name__ == "__main__":
    customtkinter.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
    customtkinter.set_default_color_theme("blue") # Themes: "blue", "green", "dark-blue"
    
    app = DesktopOrganizerApp()
    app.mainloop()
import queue
import shutil
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, scrolledtext, ttk


SORTING_RULES = {
    "Images": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"),
    "Documents": (".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".csv"),
    "Videos": (".mp4", ".mov", ".avi", ".mkv", ".flv"),
    "Audio": (".mp3", ".wav", ".aac", ".flac"),
    "Archives": (".zip", ".rar", ".tar", ".gz", ".7z"),
    "Scripts": (".py", ".js", ".html", ".css", ".sh"),
}


def get_category(filename, rules=SORTING_RULES):
    """Return the destination category for a filename, or None if unmatched."""
    extension = Path(filename).suffix.lower()
    for category, extensions in rules.items():
        if extension in extensions:
            return category
    return None


def unique_destination_path(destination_dir, filename):
    """Return a non-conflicting path in destination_dir for filename."""
    destination_dir = Path(destination_dir)
    original_path = destination_dir / filename
    if not original_path.exists():
        return original_path

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1

    while True:
        candidate = destination_dir / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def sort_folder_once(source_folder, rules=SORTING_RULES):
    """Move currently matching files in source_folder into category folders."""
    source_path = Path(source_folder)
    if not source_path.is_dir():
        raise FileNotFoundError(f"Folder does not exist: {source_path}")

    moved_files = []
    failed_files = []

    for item in source_path.iterdir():
        if not item.is_file():
            continue

        category = get_category(item.name, rules)
        if category is None:
            continue

        destination_dir = source_path / category
        destination_dir.mkdir(exist_ok=True)
        destination_path = unique_destination_path(destination_dir, item.name)

        try:
            shutil.move(str(item), str(destination_path))
            moved_files.append((item.name, category, destination_path.name))
        except OSError as exc:
            failed_files.append((item.name, str(exc)))

    return moved_files, failed_files


class DesktopOrganizerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Smart Desktop Organizer")
        self.geometry("700x550")
        self.minsize(620, 460)

        self.source_folder = ""
        self.sorting_thread = None
        self.stop_event = threading.Event()
        self.ui_queue = queue.Queue()

        self._build_styles()
        self._build_layout()
        self.after(100, self.process_ui_queue)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    @property
    def is_running(self):
        return self.sorting_thread is not None and self.sorting_thread.is_alive()

    def _build_styles(self):
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        self.style.configure("TFrame", background="#f4f6f8")
        self.style.configure("Card.TFrame", background="#ffffff", relief="flat")
        self.style.configure("TLabel", background="#f4f6f8", foreground="#17202a")
        self.style.configure("Card.TLabel", background="#ffffff", foreground="#17202a")
        self.style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        self.style.configure("Hint.TLabel", foreground="#566573")
        self.style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))

    def _build_layout(self):
        self.configure(background="#f4f6f8")

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(
            main_frame,
            text="Smart Desktop Organizer",
            style="Title.TLabel",
        )
        title_label.pack(anchor="w")

        subtitle_label = ttk.Label(
            main_frame,
            text="Choose a folder, then let the watcher sort matching files into category folders.",
            style="Hint.TLabel",
        )
        subtitle_label.pack(anchor="w", pady=(4, 18))

        source_frame = ttk.Frame(main_frame, style="Card.TFrame", padding=14)
        source_frame.pack(fill="x")
        source_frame.columnconfigure(0, weight=1)

        self.source_path_label = ttk.Label(
            source_frame,
            text="Select a folder to organize...",
            style="Card.TLabel",
            wraplength=460,
        )
        self.source_path_label.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        self.select_source_button = ttk.Button(
            source_frame,
            text="Browse Folder",
            command=self.select_source_folder,
        )
        self.select_source_button.grid(row=0, column=1)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=16)

        self.start_button = ttk.Button(
            control_frame,
            text="Start Organizing",
            command=self.start_sorting,
        )
        self.start_button.pack(side="left")

        self.stop_button = ttk.Button(
            control_frame,
            text="Stop Organizing",
            command=self.stop_sorting,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(10, 0))

        log_label = ttk.Label(main_frame, text="Activity Log")
        log_label.pack(anchor="w", pady=(8, 6))

        self.output_textbox = scrolledtext.ScrolledText(
            main_frame,
            height=12,
            wrap="word",
            font=("Consolas", 10),
            borderwidth=1,
            relief="solid",
        )
        self.output_textbox.pack(fill="both", expand=True)
        self.output_textbox.configure(state="disabled")

    def select_source_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_folder = folder_selected
            display_path = self.source_folder
            if len(display_path) > 64:
                display_path = "..." + display_path[-61:]
            self.source_path_label.configure(text=f"Monitoring: {display_path}")
            self.log_message(f"Selected folder: {self.source_folder}")

    def log_message(self, message):
        self.ui_queue.put(("log", message))

    def process_ui_queue(self):
        while True:
            try:
                action, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break

            if action == "log":
                self._append_log_message(payload)
            elif action == "stopped":
                self._set_controls_for_stopped()
                self._append_log_message(payload)

        self.after(100, self.process_ui_queue)

    def _append_log_message(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.output_textbox.configure(state="normal")
        self.output_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.output_textbox.see("end")
        self.output_textbox.configure(state="disabled")

    def start_sorting(self):
        if not self.source_folder:
            self.log_message("ERROR: Please select a source folder first.")
            return

        if not Path(self.source_folder).is_dir():
            self.log_message("ERROR: The selected folder no longer exists.")
            return

        if self.is_running:
            self.log_message("INFO: Organizer is already running.")
            return

        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.select_source_button.configure(state="disabled")
        self.log_message("Organizer started. Watching for new files...")

        self.sorting_thread = threading.Thread(target=self.sorting_process, daemon=True)
        self.sorting_thread.start()

    def stop_sorting(self):
        if not self.is_running:
            self.log_message("INFO: Organizer is not running.")
            self._set_controls_for_stopped()
            return

        self.stop_event.set()
        self._set_controls_for_stopped()
        self.log_message("Organizer stopped.")

    def _set_controls_for_stopped(self):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.select_source_button.configure(state="normal")

    def sorting_process(self):
        while not self.stop_event.is_set():
            try:
                moved_files, failed_files = sort_folder_once(self.source_folder)
            except FileNotFoundError as exc:
                self.stop_event.set()
                self.ui_queue.put(("stopped", f"ERROR: {exc}"))
                return
            except OSError as exc:
                self.log_message(f"ERROR: Could not scan folder - {exc}")
                self.stop_event.wait(5)
                continue

            for original_name, category, final_name in moved_files:
                if original_name == final_name:
                    self.log_message(f"Moved: {original_name} -> {category}")
                else:
                    self.log_message(
                        f"Moved: {original_name} -> {category} as {final_name}"
                    )

            for filename, error in failed_files:
                self.log_message(f"ERROR: Could not move {filename} - {error}")

            self.stop_event.wait(5)

    def on_closing(self):
        self.stop_event.set()
        self.destroy()


if __name__ == "__main__":
    app = DesktopOrganizerApp()
    app.mainloop()

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR / "my-website-builder"
PROJECT_APP_PATH = PROJECT_DIR / "app.py"

if not PROJECT_APP_PATH.exists():
    raise FileNotFoundError(
        f"Expected Flask app at '{PROJECT_APP_PATH}', but it was not found."
    )

project_dir_str = str(PROJECT_DIR)
if project_dir_str not in sys.path:
    sys.path.insert(0, project_dir_str)

spec = importlib.util.spec_from_file_location("website_builder_app", PROJECT_APP_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Unable to load Flask app from '{PROJECT_APP_PATH}'.")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = module.app

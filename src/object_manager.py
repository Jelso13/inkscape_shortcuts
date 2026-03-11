# src/object_manager.py

import subprocess
import logging
import time
from pathlib import Path
from Xlib import X

from src.actions import apply_style_snippet

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "inkscape_shortcuts"
OBJECTS_DIR = CONFIG_DIR / "objects"
OBJECTS_DIR.mkdir(parents=True, exist_ok=True)

def run_rofi(prompt: str, options: list[str]) -> str | None:
    """Blocks the thread, pipes options into rofi, and returns the selected string."""
    options_str = "\n".join(options) if options else ""
    try:
        result = subprocess.run(
            ['rofi', '-dmenu', '-i', '-p', prompt],
            input=options_str,
            text=True,
            capture_output=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        logger.error("Rofi is not installed on this system.")
    return None

def get_clipboard_svg() -> str | None:
    """Pulls the specific Inkscape SVG target out of the X11 clipboard."""
    try:
        result = subprocess.run(
            ['xclip', '-selection', 'c', '-o', '-target', 'image/x-inkscape-svg'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def save_object(listener) -> None:
    """The complete pipeline for saving a selected Inkscape object."""
    # 1. Fire a pristine Ctrl+C to copy the current selection
    listener.native_press('c', X.ControlMask)
    
    # CRITICAL: Wait 100ms for Inkscape to finish serializing the SVG to the clipboard
    time.sleep(0.1) 
    
    # 2. Read the copied payload
    svg_data = get_clipboard_svg()
    if not svg_data or "<svg" not in svg_data:
        logger.warning("No valid Inkscape SVG data found in clipboard. Did you select an object?")
        return

    # 3. Ask the user for a name via Rofi
    existing_files = [f.stem for f in OBJECTS_DIR.glob("*.svg")]
    
    name = run_rofi("Save object as:", existing_files)
    if not name:
        return # User pressed Escape in Rofi
        
    # 4. Save to disk
    file_path = OBJECTS_DIR / f"{name}.svg"
    file_path.write_text(svg_data)
    logger.info(f"Successfully saved object: {name}")

def load_object(listener) -> None:
    """The complete pipeline for loading and pasting an object via Rofi."""
    existing_files = [f.stem for f in OBJECTS_DIR.glob("*.svg")]
    
    if not existing_files:
        logger.warning(f"No objects found in {OBJECTS_DIR}.")
        return

    # 1. Ask the user which object to load
    name = run_rofi("Load object:", existing_files)
    if not name:
        return
        
    file_path = OBJECTS_DIR / f"{name}.svg"
    if not file_path.exists():
        return
        
    # 2. Push to clipboard
    svg_data = file_path.read_text()
    apply_style_snippet(svg_data)
    
    # 3. Paste the object natively (Ctrl + V)
    listener.native_press('v', X.ControlMask)

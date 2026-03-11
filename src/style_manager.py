"""
file used to manage predefined object styles
"""

import subprocess
import logging
import time
from pathlib import Path
from Xlib import X

from src.actions import apply_style_snippet

logger = logging.getLogger(__name__)

from src.object_manager import CONFIG_DIR, run_rofi, get_clipboard_svg

STYLES_DIR = CONFIG_DIR / "styles"
STYLES_DIR.mkdir(parents=True, exist_ok=True)

def save_style(listener) -> None:
    """The complete pipeline for saving a selected Inkscape style."""
    # 1. Fire a pristine Ctrl+C to copy the current selection's entire SVG payload
    listener.native_press('c', X.ControlMask)
    
    # CRITICAL: Wait 100ms for Inkscape to finish serializing the SVG to the clipboard
    time.sleep(0.1) 
    
    # 2. Read the copied payload
    svg_data = get_clipboard_svg()
    if not svg_data or "<svg" not in svg_data:
        logger.warning("No valid Inkscape SVG data found in clipboard. Did you select an object?")
        return

    # 3. Ask the user for a name via Rofi
    existing_files = [f.stem for f in STYLES_DIR.glob("*.svg")]
    
    name = run_rofi("Save style as:", existing_files)
    if not name:
        return 
        
    # 4. Save to disk
    file_path = STYLES_DIR / f"{name}.svg"
    file_path.write_text(svg_data)
    logger.info(f"Successfully saved style: {name}")

def load_style(listener) -> None:
    """The complete pipeline for loading and pasting a style via Rofi."""
    existing_files = [f.stem for f in STYLES_DIR.glob("*.svg")]
    
    if not existing_files:
        logger.warning(f"No styles found in {STYLES_DIR}.")
        return

    # 1. Ask the user which style to load
    name = run_rofi("Load style:", existing_files)
    if not name:
        return
        
    file_path = STYLES_DIR / f"{name}.svg"
    if not file_path.exists():
        return
        
    # 2. Push the saved SVG node to the clipboard
    svg_data = file_path.read_text()
    apply_style_snippet(svg_data)
    
    # 3. The diverging step: Paste the Style natively (Ctrl + Shift + V)
    listener.native_press('v', X.ControlMask | X.ShiftMask)

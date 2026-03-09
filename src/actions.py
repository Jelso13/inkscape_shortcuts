"""
Handler for processing actions to be taken in inkscape
"""

import subprocess
import logging

logger = logging.getLogger(__name__)

def send_keystrokes(*keys: str) -> None:
    """ Uses xdotool to send keys to inkscape """
    try:
        # Removed --sync as it is not a valid flag for the key subcommand
        subprocess.run(["xdotool", "key", "--clearmodifiers"] + list(keys), check=True)
        logger.debug(f"Sent keystrokes: {keys}")
    except subprocess.CalledProcessError as e:
            logger.error(f"Failed to send shortcut {keys}: {e}")

def apply_style_snippet(xml_snippet: str) -> None:
    """Copies an XML style snippet to the clipboard (No xdotool!)."""
    try:
        subprocess.run(
            ['xclip', '-selection', 'c', '-target', 'image/x-inkscape-svg'],
            input=xml_snippet,
            universal_newlines=True,
            check=True
        )
        logger.debug("Successfully copied style snippet to X11 clipboard.")
    except subprocess.CalledProcessError as e:
        logger.error(f"xclip failed: {e}")

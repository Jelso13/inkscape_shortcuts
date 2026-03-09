"""
Handler for processing actions to be taken in inkscape
"""

import subprocess
import logging

logger = logging.getLogger(__name__)

def send_keystrokes(*keys: str) -> None:
    """ Uses xdotool to send keys to inkscape """
    try:
        subprocess.run(["xdotool", "key"] + list(keys), check=True)
        logger.debug(f"Sent keystrokes: {keys}")
    except subprocess.CalledProcessError as e:
            logger.error(f"Failed to send shortcut {keys}: {e}")

def apply_style_snippet(xml_snippet: str) -> None:
    """Copies an XML style snippet to the clipboard and tells Inkscape to paste it."""
    try:
        subprocess.run(
            ['xclip', '-selection', 'c', '-target', 'image/x-inkscape-svg'],
            input=xml_snippet,
            universal_newlines=True,
            check=True
        )
        logger.debug("Successfully copied style snippet to X11 clipboard.")
    except subprocess.CalledProcessError as e:
        logger.error(f"xclip failed to copy style to clipboard: {e}")
        return
    except FileNotFoundError:
        logger.error("xclip is not installed. Please install it to use style snippets.")
        return

    # 2. Trigger Inkscape's native 'Paste Style' shortcut
    send_keystrokes("ctrl+shift+v")

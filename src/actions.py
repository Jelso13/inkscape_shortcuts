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
    """pastes xml style snippet"""
    pass

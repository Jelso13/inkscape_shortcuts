from Xlib import X
from Xlib.display import Display
import Xlib.error
import logging

logger = logging.getLogger(__name__)

def is_inkscape_window(window) -> bool:
    """
    Checks if a given X11 window is inkscape
    """
    try:
        window_class = window.get_wm_class()
        logger.debug(f"Checking {window_class} window")
        if window_class and "inkscape" in window_class:
            return True
    except Xlib.error.BadWindow as e:
        pass
    return False

def setup_existing_window_monitors(disp: Display) -> None:
    """
    Scans the current X11 window tree for existing Inkscape instances.
    """
    root_window = disp.screen().root
    for child_window in root_window.query_tree().children:
        if is_inkscape_window(child_window):
            logger.info(f"Found Inkscape Window with id {child_window.id}")

def setup_new_window_monitors(disp: Display) -> None:
    """
    Monitors for new inkscape windows and should add a monitor to them when they launch
    """
    root_window = disp.screen().root
    root_window.change_attributes(event_mask=X.SubstructureNotifyMask)
    logger.info("Setting up listener for new windows...")
    while True:
        event = disp.next_event()
        if event.type == X.CreateNotify:
            if is_inkscape_window(event.window):
                logger.info(f"Found Inkscape Window with id {event.window.id}")



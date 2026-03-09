from Xlib import X
from Xlib.display import Display
import Xlib.error
import logging

from src.listener import WindowListener

logger = logging.getLogger(__name__)


def get_all_windows(window):
    """
    Recursively fetches all descendents of an X11 window
    Needed because some window managers manipulate the window hierarchy 
    so that applications are collected together
    """
    windows = []
    try:
        for child in window.query_tree().children:
            windows.append(child)
            windows.extend(get_all_windows(child))
    except Xlib.error.BadWindow:
        pass
    return windows

def is_inkscape_window(window) -> bool:
    """
    Checks if a given X11 window is inkscape
    """
    try:
        window_class = window.get_wm_class()
        if window_class and "inkscape" in window_class[0].lower():
            logger.debug(f"HERE: inkscape in window class")
            return True
    except Xlib.error.BadWindow as e:
        pass
    return False

def setup_window_monitors(disp: Display) -> None:
    """
    Monitors for new inkscape windows and should add a monitor to them when they launch
    """
    root_window = disp.screen().root

    # get any existing inkscape windows first
    logger.info("Finding existing inkscape windows...")
    for child_window in get_all_windows(root_window):
        if is_inkscape_window(child_window):
            logger.info(f"Found Inkscape Window with id {child_window.id}")
            listener = WindowListener(child_window.id)
            logger.info(f"Created Listener")
            listener.start()
            logger.info(f"Created window listener and started it")

    root_window.change_attributes(event_mask=X.SubstructureNotifyMask)
    logger.info("Setting up listener for new windows...")
    while True:
        event = disp.next_event()
        if event.type == X.CreateNotify:
            if is_inkscape_window(event.window):
                logger.info(f"Found Inkscape Window with id {event.window.id}")
                listener = WindowListener(event.window.id)
                listener.start()
                logger.info(f"Created window listener and started it")



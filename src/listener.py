import threading
import logging
from Xlib import X, XK # XK = X keysim stuff
from Xlib.display import Display

logger = logging.getLogger(__name__)

class WindowListener(threading.Thread):
    """Listener thread that listens for window commands to intercept."""
    def __init__(self, window_id: int) -> None:
        logger.info(f"Initialising window listener")
        super().__init__()
        logger.info(f"Initialising window listener")
        self.window_id = window_id

    def run(self) -> None:
        """Entry point for thread.start()"""
        self.display = Display()
        self.inkscape = self.display.create_resource_object('window', self.window_id)
        logger.info(f"Starting listener for window {self.window_id}")
        self.grab()
        self.listen()

    def grab(self) -> None:
        """Tells X11 to route keys from this window to this script"""
        self.inkscape.grab_key(X.AnyKey, X.AnyModifier, True, X.GrabModeAsync, X.GrabModeAsync)
        self.inkscape.change_attributes(event_mask=X.KeyReleaseMask | X.KeyPressMask | X.StructureNotifyMask)

    def ungrab(self) -> None:
        self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)

    def listen(self) -> None:
        """Listens for key events"""
        while True:
            event = self.display.next_event()
            if event.type == X.DestroyNotify:
                if event.window.id == self.window_id:
                    logger.info(f"Window {self.window_id} closed. Stopping listener")
                    self.ungrab()
                    return
            if event.type in [X.KeyPress, X.KeyRelease]:
                if event.type == X.KeyPress:
                    keycode = event.detail
                    keysym = self.display.keycode_to_keysym(keycode, 0)
                    char = XK.keysym_to_string(keysym)
                    logger.info(f"Heard keypress {char}")
                # pass to inkscape
                self.display.allow_events(X.ReplayKeyboard, X.CurrentTime)
                self.display.flush()

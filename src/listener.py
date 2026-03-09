from src.key_handler import KeyHandler
from src.actions import send_keystrokes

import string
import threading
import logging
from Xlib import X, XK
from Xlib.display import Display

logger = logging.getLogger(__name__)

class WindowListener(threading.Thread):
    def __init__(self, window_id: int) -> None:
        super().__init__()
        self.window_id = window_id
        self.key_handler = KeyHandler({
            ("t", "g"): lambda: send_keystrokes("numbersign"),
            # ("t", "g"): lambda: send_keystrokes("numbersign", "percent"),
            ("p", "n"): lambda: send_keystrokes("F6"),
        })

        self.alphabet = list(string.ascii_lowercase + string.digits)
        self.prefixes = set(seq[0] for seq in self.key_handler.bindings.keys())

        self.event_buffer = []

    def grab_keys(self, keys_to_grab: set | list) -> None:
        self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)
        ignored_modifiers = [0, X.Mod2Mask, X.LockMask, X.Mod2Mask | X.LockMask]

        for key in keys_to_grab:
            keycode = self.string_to_keycode(key)
            if keycode:
                for mod in ignored_modifiers:
                    self.inkscape.grab_key(keycode, mod, True, X.GrabModeAsync, X.GrabModeAsync)
        self.display.sync()

    def run(self) -> None:
        self.display = Display()
        self.inkscape = self.display.create_resource_object('window', self.window_id)
        self.inkscape.change_attributes(event_mask=X.StructureNotifyMask)
        
        self.grab_keys(self.prefixes)
        self.listen()

    def string_to_keycode(self, key: str):
        keysym = XK.string_to_keysym(key)
        return self.display.keysym_to_keycode(keysym)

    def replay_events(self):
        """Replay all buffered raw X events natively to Inkscape."""
        for event in self.event_buffer:
            self.inkscape.send_event(event, propagate=True)
        self.display.flush()
        self.display.sync()
        self.event_buffer.clear()

    def listen(self) -> None:
        while True:
            event = self.display.next_event()
            
            if event.type == X.DestroyNotify and event.window.id == self.window_id:
                self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)
                return
                
            # Intercept both KeyPress and KeyRelease to protect the state machine
            elif event.type in (X.KeyPress, X.KeyRelease):
                keysym = self.display.keycode_to_keysym(event.detail, 0)
                char = XK.keysym_to_string(keysym)

                if not char:
                    self.inkscape.send_event(event, propagate=True)
                    self.display.sync()
                    continue

                # Buffer every event we intercept
                self.event_buffer.append(event)

                # Only evaluate the sequence on KeyPress
                if event.type == X.KeyPress:
                    result = self.key_handler.process_key(char)

                    if callable(result):
                        # MATCH: Execute action
                        self.event_buffer.clear() # Dump buffer; sequence consumed
                        
                        self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)
                        self.display.sync()
                        
                        result()
                        
                        self.grab_keys(self.prefixes)
                        
                    elif result is True:
                        # PARTIAL MATCH: Wait for next key
                        self.grab_keys(self.alphabet)
                        
                    elif isinstance(result, list):
                        # NO MATCH: Sequence failed.
                        self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)
                        self.display.sync()
                        
                        # Replay exactly what the user typed directly via Xlib
                        self.replay_events()
                        
                        self.grab_keys(self.prefixes)

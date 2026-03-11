from src.key_handler import KeyHandler
from src.actions import apply_style_snippet, send_keystrokes

import string
import threading
import logging
from Xlib import X, XK
from Xlib.display import Display
from Xlib.protocol import event as xevent

from src.latex_editor import spawn_latex_editor
from src.object_manager import save_object, load_object

logger = logging.getLogger(__name__)

class WindowListener(threading.Thread):
    def __init__(self, window_id: int) -> None:
        super().__init__()
        self.window_id = window_id
        self.key_handler = KeyHandler({
            ("m",): lambda: spawn_latex_editor(self, compile_latex=False), # math text
            ("M",): lambda: spawn_latex_editor(self, compile_latex=True),   # rendered math text
            ("o", "s"): lambda: save_object(self),
            ("o", "l"): lambda: load_object(self),
            ("t", "g"): lambda: send_keystrokes("numbersign"),
            ("p", "n"): lambda: send_keystrokes("F6"),
            ("u",): lambda: send_keystrokes("Ctrl+z"),
            
            # Use the new native method that is immune to your layer modifiers!
            ("s", "t"): lambda: self.paste_style("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg><inkscape:clipboard style="stroke: #FF0000; stroke-width: 2.0; fill: none;" /></svg>"""),
            
            ("s", "1"): lambda: self.paste_style("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg><inkscape:clipboard style="stroke: #00FF00; stroke-width: 2.0; fill: none;" /></svg>""") 
        })

#         self.key_handler = KeyHandler({
#             ("t", "g"): lambda: send_keystrokes("numbersign"),
#             # ("t", "g"): lambda: send_keystrokes("numbersign", "percent"),
#             ("p", "n"): lambda: send_keystrokes("F6"),
#             ("u",): lambda: send_keystrokes("Ctrl+z"),
#             ("s", "t"): lambda: apply_style_snippet("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
# <svg>
#   <inkscape:clipboard style="stroke: #FF0000; stroke-width: 2.0; fill: none;" />
# </svg>"""),
#             ("s", "1"): lambda: apply_style_snippet("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
# <svg>
#   <inkscape:clipboard style="stroke: #FF0000; stroke-width: 2.0; fill: none;" />
# </svg>""") 
#         })

        self.alphabet = list(string.ascii_lowercase + string.digits)
        self.prefixes = set(seq[0] for seq in self.key_handler.bindings.keys())

        self.event_buffer = []

    def grab_keys(self, keys_to_grab: set | list) -> None:
        self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)

        # 1. Base states we actually care about for typing/custom layouts
        base_mods = [
            0,            # Normal
            X.ShiftMask,  # Shift
            X.Mod3Mask,   # Custom Layout Layer 1
            X.Mod4Mask,   # Custom Layout Layer 2
            X.Mod5Mask,   # Custom Layout Layer 3 (AltGr)
        ]

        # 2. Status modifiers that might be active in the background
        status_mods = [
            0,
            X.Mod2Mask, # NumLock
            X.LockMask, # CapsLock
            X.Mod2Mask | X.LockMask
        ]

        # 3. Create a set of all required combinations
        modifiers_to_grab = {b | s for b in base_mods for s in status_mods}

        # 4. Temporarily silence Xlib errors so we don't spam the console 
        # if a specific combo happens to be claimed by the OS Window Manager
        old_handler = self.display.set_error_handler(lambda *args, **kwargs: None)

        for key in keys_to_grab:
            keycode = self.string_to_keycode(key)
            if keycode:
                for mod in modifiers_to_grab:
                    # Grab explicitly, bypassing the AnyModifier collision trap
                    self.inkscape.grab_key(keycode, mod, True, X.GrabModeAsync, X.GrabModeAsync)
                    
        self.display.sync()
        self.display.set_error_handler(old_handler) # Restore normal error handling

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

    def get_actual_char(self, event) -> str:
        """Translates physical keycode + modifier state into the logical character."""
        index = 0
        
        # Column 1: Shift is held
        if event.state & X.ShiftMask:
            index |= 1
            
        # Column 2: AltGr / Custom Layer is held
        # Note: Custom layout modifiers usually sit on Mod3, Mod4, or Mod5.
        if event.state & (X.Mod3Mask | X.Mod4Mask | X.Mod5Mask):
            index |= 2
            
        keysym = self.display.keycode_to_keysym(event.detail, index)
        char = XK.keysym_to_string(keysym)
        
        # Fallback to base character if the translated index is empty
        if not char:
            keysym = self.display.keycode_to_keysym(event.detail, 0)
            char = XK.keysym_to_string(keysym)
            
        return char

    def listen(self) -> None:
        while True:
            event = self.display.next_event()
            
            if event.type == X.DestroyNotify and event.window.id == self.window_id:
                self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)
                return
                
            elif event.type in (X.KeyPress, X.KeyRelease):
                # Use our new layout-aware character resolution
                char = self.get_actual_char(event)

                if not char:
                    self.inkscape.send_event(event, propagate=True)
                    self.display.sync()
                    continue

                self.event_buffer.append(event)

                if event.type == X.KeyPress:
                    result = self.key_handler.process_key(char)

                    if callable(result):
                        self.event_buffer.clear() 
                        self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)
                        self.display.sync()
                        
                        result()
                        
                        self.grab_keys(self.prefixes)
                        
                    elif result is True:
                        self.grab_keys(self.alphabet)
                        
                    elif isinstance(result, list):
                        self.inkscape.ungrab_key(X.AnyKey, X.AnyModifier)
                        self.display.sync()
                        
                        self.replay_events()
                        
                        self.grab_keys(self.prefixes)


    def native_press(self, key: str, mask: int) -> None:
        """Synthesizes a pristine X11 event, immune to physical keyboard state."""
        keycode = self.string_to_keycode(key)
        if not keycode: 
            return
        
        # 1. Build a synthetic KeyPress
        press_evt = xevent.KeyPress(
            time=X.CurrentTime,
            root=self.display.screen().root,
            window=self.inkscape,
            same_screen=0, child=X.NONE,
            root_x=0, root_y=0, event_x=0, event_y=0,
            state=mask,
            detail=keycode
        )
        
        # 2. Build a synthetic KeyRelease
        release_evt = xevent.KeyRelease(
            time=X.CurrentTime,
            root=self.display.screen().root,
            window=self.inkscape,
            same_screen=0, child=X.NONE,
            root_x=0, root_y=0, event_x=0, event_y=0,
            state=mask,
            detail=keycode
        )
        
        # 3. Fire directly at Inkscape
        self.inkscape.send_event(press_evt, propagate=True)
        self.inkscape.send_event(release_evt, propagate=True)
        self.display.flush()
        self.display.sync()

    def paste_style(self, snippet: str) -> None:
        """Handles the complete pipeline for applying a custom style."""
        apply_style_snippet(snippet)
        self.native_press('v', X.ControlMask | X.ShiftMask)

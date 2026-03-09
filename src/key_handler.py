"""
Handler for processing the keybindings
"""

import logging
from typing import Callable, Union

logger = logging.getLogger(__name__)

Action = Callable[[], None]
KeySequence = tuple[str, ...]

class KeyHandler:
    def __init__(self, bindings: dict[KeySequence, Action]) -> None:
        self.bindings = bindings
        self.buffer: list[str] = []

    def process_key(self, key_char: str) -> Union[Action, bool, list[str]]:
        self.buffer.append(key_char)
        current_sequence = tuple(self.buffer)

        # 1. EXACT MATCH
        if current_sequence in self.bindings:
            logger.info(f"Executing command for : {current_sequence}")
            action = self.bindings[current_sequence]
            self.buffer.clear()
            return action

        # 2. PARTIAL MATCH (Wait for next key)
        for sequence in self.bindings.keys():
            if sequence[:len(current_sequence)] == current_sequence:
                logger.info(f"Partial match for {current_sequence}, waiting...")
                return True

        # 3. NO MATCH: Return the buffered sequence so we can flush it!
        logger.debug(f"No match for {current_sequence}, returning buffer to flush.")
        failed_sequence = list(self.buffer)
        self.buffer.clear()
        return failed_sequence

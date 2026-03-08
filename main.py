"""
Main Entrypoint
"""

from src.window_utils import is_inkscape_window, setup_existing_window_monitors, setup_new_window_monitors

import logging
from Xlib.display import Display

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Application starting")
    
    x_display = Display()
    # set up monitors for existing inkscape windows
    setup_existing_window_monitors(x_display)

    # listen for newly opened inkscape windows and monitor those
    setup_new_window_monitors(x_display)

    x_display.close()


if __name__ == "__main__":
    main()

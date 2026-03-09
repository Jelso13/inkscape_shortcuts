"""
Main Entrypoint
"""
from src.window_utils import setup_window_monitors

import logging
from Xlib.display import Display

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Application starting")
    x_display = Display()
    setup_window_monitors(x_display)
    x_display.close()


if __name__ == "__main__":
    main()

"""
Main Entrypoint
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Application starting")
    
    # set up monitors for existing inkscape windows
    # setup_existing_window_monitors()

    # listen for newly opened inkscape windows and monitor those
    # setup_new_window_monitors()

    return


if __name__ == "__main__":
    main()

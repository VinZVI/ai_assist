#!/usr/bin/env python3
"""
Test script to verify logging with new line formatting
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from app.utils.logging import setup_logging


def main() -> None:
    """Test logging with new line formatting."""
    print("Testing logging with new line formatting...")

    # Setup logging
    setup_logging(
        log_level="INFO",
        enable_console=True,
        log_file_path=Path("logs"),
        enable_json=False,
        enable_request_logging=True,
    )

    # Test multiple log messages
    logger.info("This is the first log message")
    logger.warning("This is the second log message")
    logger.error("This is the third log message")
    logger.success("This is the fourth log message")

    print("Logging test completed.")


if __name__ == "__main__":
    main()

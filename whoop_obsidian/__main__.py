"""Main entry point for Whoop to Obsidian synchronization."""

import argparse
import locale
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import get_api_token, load_config
from .exceptions import (
    ConfigValidationError,
    DuplicateEntryError,
    VaultNotFoundError,
    WhoopAPIError,
    WhoopObsidianError,
)
from .obsidian_writer import ObsidianWriter
from .whoop_client import WhoopClient

# Lock file path
LOCK_FILE = Path(".whoop_sync.lock")

logger = logging.getLogger(__name__)


def setup_logging(config) -> None:
    """
    Set up logging configuration.

    Args:
        config: Application configuration object.
    """
    log_config = config.logging
    log_file = Path(log_config.file)

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_config.level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_config.level)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_config.rotation:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
    else:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")

    file_handler.setLevel(log_config.level)
    file_handler.setFormatter(console_formatter)
    root_logger.addHandler(file_handler)


def acquire_lock() -> bool:
    """
    Acquire lock file to prevent concurrent execution.

    Returns:
        True if lock acquired, False if already locked.
    """
    if LOCK_FILE.exists():
        logger.warning("Lock file exists. Another instance may be running.")
        return False

    try:
        LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except OSError as e:
        logger.error(f"Failed to create lock file: {e}")
        return False


def release_lock() -> None:
    """Release lock file."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except OSError as e:
        logger.warning(f"Failed to remove lock file: {e}")


def set_locale() -> None:
    """Set locale to English for consistent date formatting."""
    try:
        locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
    except locale.Error:
        try:
            # Fallback for different systems
            locale.setlocale(locale.LC_TIME, "C")
        except locale.Error:
            logger.warning("Failed to set locale to English. Date formatting may vary.")


def main() -> int:
    """
    Main application entry point.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = argparse.ArgumentParser(
        description="Sync Whoop health metrics to Obsidian vault"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate sync without writing to files",
    )

    args = parser.parse_args()

    # Set locale for English date formatting
    set_locale()

    try:
        # Load configuration
        config = load_config(args.config)

        # Set up logging
        setup_logging(config)

        logger.info("Starting Whoop to Obsidian sync")

        # Acquire lock
        if not acquire_lock():
            logger.info("Exiting due to existing lock file")
            return 0  # Exit code 0 for benign skip

        # Get API token
        api_token = get_api_token()

        # Initialize clients
        whoop_client = WhoopClient(config.whoop, api_token)
        obsidian_writer = ObsidianWriter(config)

        # Fetch metrics from Whoop
        logger.info("Fetching metrics from Whoop API")
        metrics = whoop_client.fetch_today_metrics()

        # Validate metrics
        if not whoop_client.validate_metrics(metrics):
            logger.warning("Some metrics are outside expected ranges")

        # Log fetched metrics
        logger.info(f"Fetched metrics: {metrics.model_dump(exclude_none=True)}")

        # Append to Obsidian
        if args.dry_run:
            logger.info("DRY RUN: Would append metrics to Obsidian")
            today = datetime.now()
            file_path = obsidian_writer.get_month_file_path(today)
            row = obsidian_writer._generate_table_row(metrics, today)
            logger.info(f"Target file: {file_path}")
            logger.info(f"Table row: {row}")
        else:
            logger.info("Appending metrics to Obsidian vault")
            obsidian_writer.append_metrics(metrics)

        logger.info("Sync completed successfully")
        return 0

    except ConfigValidationError as e:
        if "logger" in locals():
            logger.error(f"Configuration error: {e}")
        else:
            print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    except VaultNotFoundError as e:
        logger.error(f"Vault error: {e}")
        return 1

    except WhoopAPIError as e:
        if "401" in str(e) or "Authentication" in str(e):
            logger.error(f"Authentication error: {e}")
            return 2
        else:
            logger.error(f"API error: {e}")
            return 3

    except DuplicateEntryError as e:
        logger.info(f"Skipping duplicate entry: {e}")
        return 0  # Exit code 0 for benign skip

    except WhoopObsidianError as e:
        logger.error(f"Application error: {e}")
        return 4

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 4

    finally:
        # Always release lock
        release_lock()


if __name__ == "__main__":
    sys.exit(main())

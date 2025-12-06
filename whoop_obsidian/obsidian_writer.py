"""Obsidian markdown file operations."""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .exceptions import DuplicateEntryError, TableFormatError, VaultNotFoundError
from .models import Config, WhoopMetrics
from .template_generator import TemplateGenerator

logger = logging.getLogger(__name__)


class ObsidianWriter:
    """Handles writing health metrics to Obsidian vault files."""

    def __init__(self, config: Config):
        """
        Initialize Obsidian writer.

        Args:
            config: Application configuration object.
        """
        self.config = config
        self.vault_path = Path(config.obsidian.vault_path)
        self.file_prefix = config.obsidian.file_prefix
        self.template_generator = TemplateGenerator(config.table)

        # Validate vault path exists
        if not self.vault_path.exists():
            raise VaultNotFoundError(
                f"Obsidian vault not found at: {self.vault_path}\n"
                "Please check obsidian.vault_path in config.yaml"
            )

        if not self.vault_path.is_dir():
            raise VaultNotFoundError(
                f"Vault path is not a directory: {self.vault_path}"
            )

    def get_month_file_path(self, date: Optional[datetime] = None) -> Path:
        """
        Get file path for a given month.

        Args:
            date: Date object (defaults to today).

        Returns:
            Path object for the monthly file.
        """
        if date is None:
            date = datetime.now()

        month_name = date.strftime("%B")  # Full month name (e.g., "December")
        filename = f"{self.file_prefix}-{month_name}.md"
        return self.vault_path / filename

    def ensure_file_exists(self, file_path: Path, date: datetime) -> None:
        """
        Ensure monthly file exists, create from template if not.

        Args:
            file_path: Path to the monthly file.
            date: Date for the month (used in header).
        """
        if file_path.exists():
            logger.info(f"File already exists: {file_path}")
            return

        logger.info(f"Creating new monthly file: {file_path}")

        month_name = date.strftime("%B")
        year = date.year

        content = self.template_generator.generate_empty_file(month_name, year)

        # Write file
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Created new file: {file_path}")

    def check_duplicate_entry(self, file_path: Path, date: datetime) -> bool:
        """
        Check if entry for given date already exists in file.

        Args:
            file_path: Path to the monthly file.
            date: Date to check for.

        Returns:
            True if duplicate exists, False otherwise.
        """
        if not file_path.exists():
            return False

        content = file_path.read_text(encoding="utf-8")
        date_str = self.template_generator.format_date(date)

        # Look for date in table rows
        # Table row format: | date | ... |
        pattern = rf"\|\s*{re.escape(date_str)}\s*\|"

        return bool(re.search(pattern, content))

    def append_metrics(
        self, metrics: WhoopMetrics, date: Optional[datetime] = None
    ) -> None:
        """
        Append metrics row to monthly file.

        Args:
            metrics: Metrics data to append.
            date: Date for the entry (defaults to today).

        Raises:
            DuplicateEntryError: If entry already exists and deduplication is enabled.
            TableFormatError: If table structure is invalid.
        """
        if date is None:
            date = datetime.now()

        file_path = self.get_month_file_path(date)

        # Ensure file exists
        self.ensure_file_exists(file_path, date)

        # Check for duplicates if deduplication is enabled
        if self.config.execution.deduplication:
            if self.check_duplicate_entry(file_path, date):
                raise DuplicateEntryError(
                    f"Entry for {date.strftime('%Y-%m-%d')} already exists in {file_path.name}"
                )

        # Generate table row
        row = self._generate_table_row(metrics, date)

        # Append to file using atomic write
        self._append_row_atomic(file_path, row)

        logger.info(f"Appended metrics for {date.strftime('%Y-%m-%d')} to {file_path.name}")

    def _generate_table_row(self, metrics: WhoopMetrics, date: datetime) -> str:
        """
        Generate markdown table row from metrics.

        Args:
            metrics: Metrics data.
            date: Date for the entry.

        Returns:
            Formatted table row string.
        """
        cells = []

        for column in self.config.table.columns:
            if column.type == "date":
                cell_value = self.template_generator.format_date(date)
            elif column.type == "metric":
                metric_value = metrics.get_metric(column.metric_key)
                cell_value = self.template_generator.format_metric_value(
                    metric_value, column.decimal_places
                )
            elif column.type == "custom":
                cell_value = ""
            else:
                cell_value = ""

            cells.append(cell_value)

        return "| " + " | ".join(cells) + " |"

    def _append_row_atomic(self, file_path: Path, row: str) -> None:
        """
        Append row to file using atomic write strategy.

        Args:
            file_path: Path to the file.
            row: Table row to append.

        Raises:
            TableFormatError: If file operation fails.
        """
        try:
            # Read current content
            content = file_path.read_text(encoding="utf-8")

            # Append new row
            new_content = content.rstrip() + "\n" + row + "\n"

            # Write to temporary file
            temp_path = file_path.parent / f".{file_path.name}.tmp"
            temp_path.write_text(new_content, encoding="utf-8")

            # Atomic rename
            temp_path.replace(file_path)

        except OSError as e:
            raise TableFormatError(f"Failed to write to file {file_path}: {e}")

    def validate_table_structure(self, file_path: Path) -> bool:
        """
        Validate that file has expected table structure.

        Args:
            file_path: Path to the file to validate.

        Returns:
            True if structure is valid, False otherwise.
        """
        if not file_path.exists():
            return False

        try:
            content = file_path.read_text(encoding="utf-8")

            # Look for table header row
            # Expected format: | Col1 | Col2 | ... |
            lines = content.split("\n")

            table_started = False
            for i, line in enumerate(lines):
                if line.strip().startswith("|") and not table_started:
                    # Found potential table header
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Check if next line is separator (contains dashes)
                        if "|" in next_line and "-" in next_line:
                            table_started = True

                            # Extract column names from header
                            header_cols = [
                                col.strip()
                                for col in line.split("|")
                                if col.strip()
                            ]

                            # Extract expected column names from config
                            expected_cols = [
                                col.name for col in self.config.table.columns
                            ]

                            if header_cols != expected_cols:
                                logger.warning(
                                    f"Table structure mismatch in {file_path.name}:\n"
                                    f"  Expected: {expected_cols}\n"
                                    f"  Found:    {header_cols}"
                                )
                                return False

                            return True

            return False

        except Exception as e:
            logger.error(f"Failed to validate table structure: {e}")
            return False

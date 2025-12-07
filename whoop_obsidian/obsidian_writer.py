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
        year = date.year
        filename = f"Health Metrics - {month_name} {year}.md"
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
        Append metrics row to monthly file. Также добавляет пропущенные дни месяца.
        """
        from calendar import monthrange
        if date is None:
            date = datetime.now()
        file_path = self.get_month_file_path(date)
        self.ensure_file_exists(file_path, date)
        
        # Заполняем пропущенные дни
        year, month = date.year, date.month
        num_days = monthrange(year, month)[1]
        existing_dates = set()
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("|"):
                    parts = line.split("|")
                    if len(parts) > 1:
                        existing_dates.add(parts[1].strip())
        from whoop_obsidian.config import get_api_token
        from whoop_obsidian.whoop_client import WhoopClient
        api_token = get_api_token()
        whoop_client = WhoopClient(self.config.whoop, api_token)
        for day in range(1, date.day):
            date_obj = datetime(year, month, day)
            date_str = self.template_generator.format_date(date_obj)
            if date_str not in existing_dates:
                logger.info(f"Fetching metrics for {date_str}")
                past_metrics = self._fetch_metrics_for_date(whoop_client, date_obj)
                row = self._generate_table_row(past_metrics, date_obj)
                self._append_row_atomic(file_path, row)
        
        # Проверка на дубликаты для текущей даты
        if self.config.execution.deduplication:
            if self.check_duplicate_entry(file_path, date):
                raise DuplicateEntryError(
                    f"Entry for {date.strftime('%Y-%m-%d')} already exists in {file_path.name}"
                )
        
        # Генерация и добавление строки для текущей даты
        row = self._generate_table_row(metrics, date)
        self._append_row_atomic(file_path, row)
        logger.info(f"Appended metrics for {date.strftime('%Y-%m-%d')} to {file_path.name}")

    def _fetch_metrics_for_date(self, whoop_client, date_obj):
        """
        Получить метрики за конкретный день через WhoopClient.
        """
        from datetime import timedelta
        start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        start_iso = start_of_day.isoformat() + "Z"
        end_iso = end_of_day.isoformat() + "Z"
        try:
            metrics = whoop_client.fetch_metrics_for_range(start_iso, end_iso)
            return metrics
        except Exception:
            return WhoopMetrics()

    def _add_color_indicator(self, value: float, metric_key: str) -> str:
        """
        Add color emoji indicator based on threshold ranges.
        
        Args:
            value: Metric value
            metric_key: Key to identify which thresholds to use
            
        Returns:
            Emoji indicator (🟢 green, 🟡 yellow, 🔴 red)
        """
        # Thresholds based on PROJECT_PLAN.md
        thresholds = {
            "sleep_score": {"green": (85, 100), "yellow": (70, 84), "red": (0, 69)},
            "recovery_score": {"green": (67, 100), "yellow": (34, 66), "red": (0, 33)},
            "strain_score": {"green": (0, 14), "yellow": (15, 18), "red": (19, 21)},
        }
        
        if metric_key not in thresholds:
            return ""
        
        ranges = thresholds[metric_key]
        
        if ranges["green"][0] <= value <= ranges["green"][1]:
            return "🟢"
        elif ranges["yellow"][0] <= value <= ranges["yellow"][1]:
            return "🟡"
        elif ranges["red"][0] <= value <= ranges["red"][1]:
            return "🔴"
        
        return ""

    def _generate_table_row(self, metrics: WhoopMetrics, date: datetime) -> str:
        """
        Generate markdown table row from metrics, поддержка custom_sleep.
        """
        cells = []
        for column in self.config.table.columns:
            if column.type == "date":
                cell_value = self.template_generator.format_date(date)
            elif column.type == "custom_sleep":
                score = metrics.sleep_score if metrics.sleep_score is not None else ""
                # Use sleep_duration_minutes (actual sleep time) instead of total time in bed
                duration_minutes = metrics.sleep_duration_minutes if metrics.sleep_duration_minutes is not None else None
                
                if score != "" and duration_minutes is not None:
                    # Format as HH:MM with color indicator
                    hours = duration_minutes // 60
                    minutes = duration_minutes % 60
                    color = self._add_color_indicator(score, "sleep_score")
                    cell_value = f"{color} {int(round(score))} ({hours}:{minutes:02d})" if color else f"{int(round(score))} ({hours}:{minutes:02d})"
                elif score != "":
                    color = self._add_color_indicator(score, "sleep_score")
                    cell_value = f"{color} {int(round(score))}" if color else f"{int(round(score))}"
                elif duration_minutes is not None:
                    hours = duration_minutes // 60
                    minutes = duration_minutes % 60
                    cell_value = f"({hours}:{minutes:02d})"
                else:
                    cell_value = ""
            elif column.type == "metric":
                metric_value = metrics.get_metric(column.metric_key)
                if metric_value is not None:
                    color = self._add_color_indicator(metric_value, column.metric_key)
                    formatted_value = self.template_generator.format_metric_value(
                        metric_value, column.decimal_places
                    )
                    cell_value = f"{color} {formatted_value}" if color else formatted_value
                else:
                    cell_value = ""
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

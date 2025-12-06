"""Template generation for Obsidian markdown files."""

from datetime import datetime
from typing import Optional

from .models import TableConfig


class TemplateGenerator:
    """Generates markdown templates for Obsidian files."""

    def __init__(self, table_config: TableConfig):
        """
        Initialize template generator.

        Args:
            table_config: Table configuration object.
        """
        self.table_config = table_config

    def generate_file_header(self, month: str, year: int) -> str:
        """
        Generate markdown file header.

        Args:
            month: Month name (e.g., "December").
            year: Year as integer.

        Returns:
            Markdown header string.
        """
        return f"# Health Metrics - {month} {year}\n\n"

    def generate_table_header(self) -> str:
        """
        Generate markdown table header with column names and alignment.

        Returns:
            Markdown table header string (header + separator lines).
        """
        columns = self.table_config.columns

        # Generate column names row
        header_row = "| " + " | ".join(col.name for col in columns) + " |"

        # Generate separator row with alignment
        separators = []
        for col in columns:
            # Match separator length to column name length
            sep_len = len(col.name)
            if self.table_config.alignment == "left":
                separators.append("-" * sep_len)
            elif self.table_config.alignment == "center":
                # Center alignment: :---:
                separators.append(":" + "-" * (sep_len - 2) + ":")
            elif self.table_config.alignment == "right":
                # Right alignment: ----:
                separators.append("-" * (sep_len - 1) + ":")
            else:
                separators.append("-" * sep_len)

        separator_row = "|" + "|".join(separators) + "|"

        return f"{header_row}\n{separator_row}\n"

    def generate_empty_file(self, month: str, year: int) -> str:
        """
        Generate complete empty markdown file with header and table structure.

        Args:
            month: Month name (e.g., "December").
            year: Year as integer.

        Returns:
            Complete markdown file content as string.
        """
        header = self.generate_file_header(month, year)
        table_header = self.generate_table_header()
        return header + table_header

    def format_metric_value(
        self, value: Optional[float], decimal_places: int = 0
    ) -> str:
        """
        Format metric value for table cell.

        Args:
            value: Metric value to format.
            decimal_places: Number of decimal places to display.

        Returns:
            Formatted value string, or empty string if value is None.
        """
        if value is None:
            return ""

        if decimal_places == 0:
            return str(int(round(value)))
        else:
            return f"{value:.{decimal_places}f}"

    def format_date(self, date: datetime) -> str:
        """
        Format date according to configured format.

        Args:
            date: Date to format.

        Returns:
            Formatted date string.
        """
        # Convert date_format to strftime format
        # MM/DD -> %m/%d
        fmt = self.table_config.date_format
        fmt = fmt.replace("MM", "%m").replace("DD", "%d")

        return date.strftime(fmt)

    def get_alignment_separator(self) -> str:
        """
        Get table separator based on alignment setting.

        Returns:
            Separator string for markdown table.
        """
        if self.table_config.alignment == "left":
            return "------"
        elif self.table_config.alignment == "center":
            return ":----:"
        elif self.table_config.alignment == "right":
            return "-----:"
        else:
            return "------"

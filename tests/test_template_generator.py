"""Tests for template generator."""

from datetime import datetime

import pytest

from whoop_obsidian.models import TableColumn, TableConfig
from whoop_obsidian.template_generator import TemplateGenerator


@pytest.fixture
def basic_table_config():
    """Create basic table configuration for testing."""
    return TableConfig(
        date_format="MM/DD",
        columns=[
            TableColumn(name="Date", type="date"),
            TableColumn(name="Sleep Score", type="metric", metric_key="sleep_score"),
            TableColumn(name="Notes", type="custom"),
        ],
        alignment="left",
    )


class TestTemplateGenerator:
    """Tests for TemplateGenerator class."""

    def test_generate_file_header(self, basic_table_config):
        """Test file header generation."""
        generator = TemplateGenerator(basic_table_config)
        header = generator.generate_file_header("December", 2024)
        assert header == "# Health Metrics - December 2024\n\n"

    def test_generate_table_header_left_aligned(self, basic_table_config):
        """Test table header generation with left alignment."""
        generator = TemplateGenerator(basic_table_config)
        header = generator.generate_table_header()

        expected = (
            "| Date | Sleep Score | Notes |\n"
            "|----|-----------|-----|\n"
        )
        assert header == expected

    def test_generate_table_header_center_aligned(self):
        """Test table header generation with center alignment."""
        config = TableConfig(
            date_format="MM/DD",
            columns=[
                TableColumn(name="Date", type="date"),
                TableColumn(name="Score", type="metric", metric_key="score"),
            ],
            alignment="center",
        )
        generator = TemplateGenerator(config)
        header = generator.generate_table_header()

        expected = "| Date | Score |\n|:--:|:---:|\n"
        assert header == expected

    def test_generate_table_header_right_aligned(self):
        """Test table header generation with right alignment."""
        config = TableConfig(
            date_format="MM/DD",
            columns=[
                TableColumn(name="Date", type="date"),
                TableColumn(name="Score", type="metric", metric_key="score"),
            ],
            alignment="right",
        )
        generator = TemplateGenerator(config)
        header = generator.generate_table_header()

        expected = "| Date | Score |\n|---:|----:|\n"
        assert header == expected

    def test_generate_empty_file(self, basic_table_config):
        """Test complete empty file generation."""
        generator = TemplateGenerator(basic_table_config)
        content = generator.generate_empty_file("December", 2024)

        assert content.startswith("# Health Metrics - December 2024\n\n")
        assert "| Date | Sleep Score | Notes |" in content
        assert "|----|-----------|-----|" in content

    def test_format_metric_value_integer(self, basic_table_config):
        """Test formatting metric value as integer."""
        generator = TemplateGenerator(basic_table_config)
        result = generator.format_metric_value(85.7, decimal_places=0)
        assert result == "86"  # Rounded

    def test_format_metric_value_decimal(self, basic_table_config):
        """Test formatting metric value with decimals."""
        generator = TemplateGenerator(basic_table_config)
        result = generator.format_metric_value(7.523, decimal_places=1)
        assert result == "7.5"

    def test_format_metric_value_none(self, basic_table_config):
        """Test formatting None value."""
        generator = TemplateGenerator(basic_table_config)
        result = generator.format_metric_value(None, decimal_places=0)
        assert result == ""

    def test_format_date(self, basic_table_config):
        """Test date formatting."""
        generator = TemplateGenerator(basic_table_config)
        date = datetime(2024, 12, 5)
        result = generator.format_date(date)
        assert result == "12/05"

    def test_format_date_single_digit_month(self):
        """Test date formatting with single digit month."""
        config = TableConfig(
            date_format="MM/DD",
            columns=[TableColumn(name="Date", type="date")],
            alignment="left",
        )
        generator = TemplateGenerator(config)
        date = datetime(2024, 3, 15)
        result = generator.format_date(date)
        assert result == "03/15"

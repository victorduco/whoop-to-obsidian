"""Tests for Obsidian writer."""

from datetime import datetime
from pathlib import Path

import pytest

from whoop_obsidian.exceptions import DuplicateEntryError, VaultNotFoundError
from whoop_obsidian.models import (
    Config,
    ExecutionConfig,
    LoggingConfig,
    ObsidianConfig,
    ScheduleConfig,
    TableColumn,
    TableConfig,
    WhoopConfig,
    WhoopMetrics,
)
from whoop_obsidian.obsidian_writer import ObsidianWriter


@pytest.fixture
def test_config(tmp_path):
    """Create test configuration."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    return Config(
        whoop=WhoopConfig(
            base_url="https://api.whoop.com/v1",
            metrics=["sleep_score", "recovery_score"],
            timeout_seconds=30,
        ),
        obsidian=ObsidianConfig(
            vault_path=str(vault_path),
            file_prefix="health",
        ),
        table=TableConfig(
            date_format="MM/DD",
            columns=[
                TableColumn(name="Date", type="date"),
                TableColumn(name="Sleep Score", type="metric", metric_key="sleep_score"),
                TableColumn(name="Recovery", type="metric", metric_key="recovery_score"),
                TableColumn(name="Notes", type="custom"),
            ],
            alignment="left",
        ),
        schedule=ScheduleConfig(run_time="11:00"),
        logging=LoggingConfig(level="INFO", file="logs/test.log", rotation=True),
        execution=ExecutionConfig(
            timezone="local",
            allow_historical=False,
            deduplication=True,
        ),
    )


class TestObsidianWriter:
    """Tests for ObsidianWriter class."""

    def test_init_valid_vault(self, test_config):
        """Test initialization with valid vault path."""
        writer = ObsidianWriter(test_config)
        assert writer.vault_path.exists()
        assert writer.file_prefix == "health"

    def test_init_missing_vault_raises_error(self, test_config):
        """Test initialization with missing vault raises error."""
        test_config.obsidian.vault_path = "/nonexistent/vault"
        with pytest.raises(VaultNotFoundError):
            ObsidianWriter(test_config)

    def test_get_month_file_path(self, test_config):
        """Test getting month file path."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        file_path = writer.get_month_file_path(date)

        assert file_path.name == "health-December.md"
        assert file_path.parent == writer.vault_path

    def test_ensure_file_exists_creates_new_file(self, test_config):
        """Test that ensure_file_exists creates new file."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        file_path = writer.get_month_file_path(date)

        assert not file_path.exists()

        writer.ensure_file_exists(file_path, date)

        assert file_path.exists()
        content = file_path.read_text()
        assert "# Health Metrics - December 2024" in content
        assert "| Date | Sleep Score | Recovery | Notes |" in content

    def test_ensure_file_exists_preserves_existing_file(self, test_config):
        """Test that ensure_file_exists doesn't overwrite existing file."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        file_path = writer.get_month_file_path(date)

        # Create file with some content
        original_content = "# Test content\n"
        file_path.write_text(original_content)

        writer.ensure_file_exists(file_path, date)

        # Content should be unchanged
        assert file_path.read_text() == original_content

    def test_check_duplicate_entry(self, test_config):
        """Test duplicate entry detection."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        file_path = writer.get_month_file_path(date)

        # Create file with entry for 12/05
        content = (
            "# Health Metrics - December 2024\n\n"
            "| Date | Sleep Score | Recovery | Notes |\n"
            "|------|-------------|----------|-------|\n"
            "| 12/05 | 85 | 72 | |\n"
        )
        file_path.write_text(content)

        # Check for duplicate
        assert writer.check_duplicate_entry(file_path, date) is True

        # Check for non-duplicate
        other_date = datetime(2024, 12, 6)
        assert writer.check_duplicate_entry(file_path, other_date) is False

    def test_generate_table_row(self, test_config):
        """Test table row generation."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        metrics = WhoopMetrics(
            sleep_score=85.0,
            recovery_score=72.0,
        )

        row = writer._generate_table_row(metrics, date)
        assert row == "| 12/05 | 85 | 72 |  |"

    def test_generate_table_row_with_missing_metrics(self, test_config):
        """Test table row generation with missing metrics."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        metrics = WhoopMetrics(
            sleep_score=85.0,
            # recovery_score is None
        )

        row = writer._generate_table_row(metrics, date)
        assert row == "| 12/05 | 85 |  |  |"  # Empty cell for missing recovery

    def test_append_metrics(self, test_config):
        """Test appending metrics to file."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        metrics = WhoopMetrics(
            sleep_score=85.0,
            recovery_score=72.0,
        )

        writer.append_metrics(metrics, date)

        file_path = writer.get_month_file_path(date)
        assert file_path.exists()

        content = file_path.read_text()
        assert "| 12/05 | 85 | 72 |  |" in content

    def test_append_metrics_raises_duplicate_error(self, test_config):
        """Test that appending duplicate entry raises error."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        metrics = WhoopMetrics(
            sleep_score=85.0,
            recovery_score=72.0,
        )

        # First append should succeed
        writer.append_metrics(metrics, date)

        # Second append should raise duplicate error
        with pytest.raises(DuplicateEntryError):
            writer.append_metrics(metrics, date)

    def test_append_metrics_allows_duplicate_if_disabled(self, test_config):
        """Test that duplicate is allowed when deduplication is disabled."""
        test_config.execution.deduplication = False
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        metrics = WhoopMetrics(
            sleep_score=85.0,
            recovery_score=72.0,
        )

        # Both appends should succeed
        writer.append_metrics(metrics, date)
        writer.append_metrics(metrics, date)

        file_path = writer.get_month_file_path(date)
        content = file_path.read_text()

        # Should have two identical rows
        assert content.count("| 12/05 | 85 | 72 |  |") == 2

    def test_validate_table_structure(self, test_config):
        """Test table structure validation."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        file_path = writer.get_month_file_path(date)

        # Create file with correct structure
        writer.ensure_file_exists(file_path, date)

        assert writer.validate_table_structure(file_path) is True

    def test_validate_table_structure_mismatched_columns(self, test_config):
        """Test validation fails with mismatched columns."""
        writer = ObsidianWriter(test_config)
        date = datetime(2024, 12, 5)
        file_path = writer.get_month_file_path(date)

        # Create file with different columns
        content = (
            "# Health Metrics - December 2024\n\n"
            "| Date | Different Column |\n"
            "|------|------------------|\n"
        )
        file_path.write_text(content)

        assert writer.validate_table_structure(file_path) is False

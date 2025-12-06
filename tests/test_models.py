"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from whoop_obsidian.models import (
    Config,
    ObsidianConfig,
    ScheduleConfig,
    TableColumn,
    TableConfig,
    WhoopConfig,
    WhoopMetrics,
)


class TestWhoopConfig:
    """Tests for WhoopConfig model."""

    def test_valid_config(self):
        """Test valid Whoop configuration."""
        config = WhoopConfig(
            base_url="https://api.whoop.com/v1",
            metrics=["sleep_score", "recovery_score"],
            timeout_seconds=30,
        )
        assert config.base_url == "https://api.whoop.com/v1"
        assert len(config.metrics) == 2
        assert config.timeout_seconds == 30

    def test_empty_metrics_raises_error(self):
        """Test that empty metrics list raises validation error."""
        with pytest.raises(ValidationError):
            WhoopConfig(
                base_url="https://api.whoop.com/v1",
                metrics=[],
                timeout_seconds=30,
            )


class TestObsidianConfig:
    """Tests for ObsidianConfig model."""

    def test_valid_absolute_path(self):
        """Test valid absolute path."""
        config = ObsidianConfig(
            vault_path="/Users/test/vault",
            file_prefix="health",
        )
        assert config.vault_path == "/Users/test/vault"
        assert config.file_prefix == "health"

    def test_relative_path_raises_error(self):
        """Test that relative path raises validation error."""
        with pytest.raises(ValidationError):
            ObsidianConfig(
                vault_path="relative/path",
                file_prefix="health",
            )

    def test_invalid_file_prefix_raises_error(self):
        """Test that invalid file prefix raises validation error."""
        with pytest.raises(ValidationError):
            ObsidianConfig(
                vault_path="/Users/test/vault",
                file_prefix="health@test",  # @ is not allowed
            )

    def test_valid_file_prefix_with_dash_underscore(self):
        """Test that dash and underscore are allowed in prefix."""
        config = ObsidianConfig(
            vault_path="/Users/test/vault",
            file_prefix="health-metrics_2024",
        )
        assert config.file_prefix == "health-metrics_2024"


class TestTableColumn:
    """Tests for TableColumn model."""

    def test_date_column(self):
        """Test date type column."""
        column = TableColumn(name="Date", type="date")
        assert column.name == "Date"
        assert column.type == "date"
        assert column.metric_key is None

    def test_metric_column_with_key(self):
        """Test metric type column with metric_key."""
        column = TableColumn(
            name="Sleep Score",
            type="metric",
            metric_key="sleep_score",
        )
        assert column.name == "Sleep Score"
        assert column.type == "metric"
        assert column.metric_key == "sleep_score"

    def test_metric_column_without_key_raises_error(self):
        """Test that metric column without metric_key raises error."""
        with pytest.raises(ValidationError):
            TableColumn(name="Sleep Score", type="metric")

    def test_custom_column(self):
        """Test custom type column."""
        column = TableColumn(name="Notes", type="custom")
        assert column.name == "Notes"
        assert column.type == "custom"


class TestTableConfig:
    """Tests for TableConfig model."""

    def test_valid_table_config(self):
        """Test valid table configuration."""
        config = TableConfig(
            date_format="MM/DD",
            columns=[
                TableColumn(name="Date", type="date"),
                TableColumn(name="Sleep", type="metric", metric_key="sleep_score"),
            ],
            alignment="left",
        )
        assert config.date_format == "MM/DD"
        assert len(config.columns) == 2
        assert config.alignment == "left"

    def test_empty_columns_raises_error(self):
        """Test that empty columns list raises error."""
        with pytest.raises(ValidationError):
            TableConfig(
                date_format="MM/DD",
                columns=[],
                alignment="left",
            )

    def test_no_date_column_raises_error(self):
        """Test that missing date column raises error."""
        with pytest.raises(ValidationError):
            TableConfig(
                date_format="MM/DD",
                columns=[
                    TableColumn(name="Sleep", type="metric", metric_key="sleep_score"),
                ],
                alignment="left",
            )


class TestScheduleConfig:
    """Tests for ScheduleConfig model."""

    def test_valid_time_format(self):
        """Test valid time format."""
        config = ScheduleConfig(run_time="11:00")
        assert config.run_time == "11:00"

    def test_invalid_time_format_raises_error(self):
        """Test that invalid time format raises error."""
        with pytest.raises(ValidationError):
            ScheduleConfig(run_time="25:00")  # Invalid hour

        with pytest.raises(ValidationError):
            ScheduleConfig(run_time="11:60")  # Invalid minute

        with pytest.raises(ValidationError):
            ScheduleConfig(run_time="11am")  # Wrong format


class TestWhoopMetrics:
    """Tests for WhoopMetrics model."""

    def test_all_metrics(self):
        """Test metrics with all values."""
        metrics = WhoopMetrics(
            sleep_score=85.0,
            sleep_duration=7.5,
            recovery_score=72.0,
            strain_score=12.3,
            hrv=65.0,
            timestamp="2024-12-01T10:00:00Z",
        )
        assert metrics.sleep_score == 85.0
        assert metrics.sleep_duration == 7.5
        assert metrics.recovery_score == 72.0
        assert metrics.strain_score == 12.3
        assert metrics.hrv == 65.0

    def test_partial_metrics(self):
        """Test metrics with some None values."""
        metrics = WhoopMetrics(
            sleep_score=85.0,
            recovery_score=72.0,
        )
        assert metrics.sleep_score == 85.0
        assert metrics.recovery_score == 72.0
        assert metrics.sleep_duration is None
        assert metrics.strain_score is None

    def test_get_metric(self):
        """Test get_metric method."""
        metrics = WhoopMetrics(
            sleep_score=85.0,
            recovery_score=72.0,
        )
        assert metrics.get_metric("sleep_score") == 85.0
        assert metrics.get_metric("recovery_score") == 72.0
        assert metrics.get_metric("strain_score") is None
        assert metrics.get_metric("unknown") is None

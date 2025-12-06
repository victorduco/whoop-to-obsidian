"""Pydantic data models for configuration and API responses."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re
from pathlib import Path


class WhoopConfig(BaseModel):
    """Whoop API configuration."""

    base_url: str = Field(default="https://api.whoop.com/v1")
    metrics: list[str] = Field(min_length=1)
    timeout_seconds: int = Field(default=30, ge=1, le=300)

    @field_validator("metrics")
    @classmethod
    def validate_metrics(cls, v: list[str]) -> list[str]:
        """Validate that metrics list is not empty."""
        if not v:
            raise ValueError("metrics list cannot be empty")
        return v


class ObsidianConfig(BaseModel):
    """Obsidian vault configuration."""

    vault_path: str
    file_prefix: str

    @field_validator("vault_path")
    @classmethod
    def validate_vault_path(cls, v: str) -> str:
        """Validate that vault path is absolute."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("vault_path must be an absolute path")
        return v

    @field_validator("file_prefix")
    @classmethod
    def validate_file_prefix(cls, v: str) -> str:
        """Validate that file prefix contains only allowed characters."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "file_prefix must contain only alphanumeric characters, dashes, and underscores"
            )
        return v


class TableColumn(BaseModel):
    """Configuration for a single table column."""

    name: str
    type: Literal["date", "metric", "custom"]
    metric_key: Optional[str] = None
    decimal_places: int = Field(default=0, ge=0, le=5)

    @model_validator(mode="after")
    def validate_metric_key(self) -> "TableColumn":
        """Validate that metric columns have metric_key."""
        if self.type == "metric" and not self.metric_key:
            raise ValueError(f"Column '{self.name}' of type 'metric' must have metric_key")
        return self


class TableConfig(BaseModel):
    """Table structure configuration."""

    date_format: str = Field(default="MM/DD")
    columns: list[TableColumn] = Field(min_length=1)
    alignment: Literal["left", "center", "right"] = Field(default="left")

    @field_validator("columns")
    @classmethod
    def validate_columns(cls, v: list[TableColumn]) -> list[TableColumn]:
        """Validate that columns list is not empty and has a date column."""
        if not v:
            raise ValueError("columns list cannot be empty")

        # Check for at least one date column
        has_date = any(col.type == "date" for col in v)
        if not has_date:
            raise ValueError("columns must include at least one column of type 'date'")

        return v


class ThresholdRange(BaseModel):
    """Threshold range for metric coloring."""

    green: list[int] = Field(min_length=2, max_length=2)
    yellow: list[int] = Field(min_length=2, max_length=2)
    red: list[int] = Field(min_length=2, max_length=2)


class ScheduleConfig(BaseModel):
    """Scheduling configuration."""

    run_time: str

    @field_validator("run_time")
    @classmethod
    def validate_run_time(cls, v: str) -> str:
        """Validate time format is HH:MM."""
        if not re.match(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", v):
            raise ValueError("run_time must be in HH:MM format (24-hour)")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    file: str = Field(default="logs/whoop_sync.log")
    rotation: bool = Field(default=True)


class ExecutionConfig(BaseModel):
    """Execution behavior configuration."""

    timezone: str = Field(default="local")
    allow_historical: bool = Field(default=False)
    deduplication: bool = Field(default=True)


class Config(BaseModel):
    """Main configuration model."""

    whoop: WhoopConfig
    obsidian: ObsidianConfig
    table: TableConfig
    thresholds: dict[str, ThresholdRange] = Field(default_factory=dict)
    schedule: ScheduleConfig
    logging: LoggingConfig
    execution: ExecutionConfig


class WhoopMetrics(BaseModel):
    """Whoop API metrics response."""

    sleep_score: Optional[float] = None
    sleep_duration: Optional[float] = None
    recovery_score: Optional[float] = None
    strain_score: Optional[float] = None
    hrv: Optional[float] = None
    timestamp: Optional[str] = None

    def get_metric(self, key: str) -> Optional[float]:
        """Get metric value by key."""
        return getattr(self, key, None)

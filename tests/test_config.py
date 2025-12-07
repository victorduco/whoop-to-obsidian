"""Tests for configuration loading."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from whoop_obsidian.config import get_api_token, load_config
from whoop_obsidian.exceptions import ConfigValidationError


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, tmp_path):
        """Test loading valid configuration file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "whoop": {
                "base_url": "https://api.whoop.com/v1",
                "metrics": ["sleep_score", "recovery_score"],
                "timeout_seconds": 30,
            },
            "obsidian": {
                "vault_path": "/tmp/vault",
                "file_prefix": "health",
            },
            "table": {
                "date_format": "MM/DD",
                "columns": [
                    {"name": "Date", "type": "date"},
                    {
                        "name": "Sleep Score",
                        "type": "metric",
                        "metric_key": "sleep_score",
                    },
                ],
                "alignment": "left",
            },
            "schedule": {"run_time": "11:00"},
            "logging": {
                "level": "INFO",
                "file": "logs/whoop_sync.log",
                "rotation": True,
            },
            "execution": {
                "timezone": "local",
                "allow_historical": False,
                "deduplication": True,
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(str(config_file))
        assert config.whoop.base_url == "https://api.whoop.com/v1"
        assert len(config.whoop.metrics) == 2
        assert config.obsidian.vault_path == "/tmp/vault"
        assert config.obsidian.file_prefix == "health"

    def test_load_missing_config_raises_error(self):
        """Test that missing config file raises error."""
        with pytest.raises(ConfigValidationError, match="Configuration file not found"):
            load_config("/nonexistent/config.yaml")

    def test_load_invalid_yaml_raises_error(self, tmp_path):
        """Test that invalid YAML raises error."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigValidationError, match="Failed to parse YAML"):
            load_config(str(config_file))

    def test_load_invalid_schema_raises_error(self, tmp_path):
        """Test that invalid config schema raises error."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "whoop": {
                "base_url": "https://api.whoop.com/v1",
                "metrics": [],  # Empty metrics - invalid
                "timeout_seconds": 30,
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ConfigValidationError, match="Configuration validation failed"):
            load_config(str(config_file))

    def test_load_config_with_env_variable(self, tmp_path, monkeypatch):
        """Test loading config using environment variable."""
        config_file = tmp_path / "custom_config.yaml"
        config_data = {
            "whoop": {
                "base_url": "https://api.whoop.com/v1",
                "metrics": ["sleep_score"],
                "timeout_seconds": 30,
            },
            "obsidian": {
                "vault_path": "/tmp/vault",
                "file_prefix": "health",
            },
            "table": {
                "date_format": "MM/DD",
                "columns": [{"name": "Date", "type": "date"}],
                "alignment": "left",
            },
            "schedule": {"run_time": "11:00"},
            "logging": {
                "level": "INFO",
                "file": "logs/whoop_sync.log",
                "rotation": True,
            },
            "execution": {
                "timezone": "local",
                "allow_historical": False,
                "deduplication": True,
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setenv("WHOOP_CONFIG_PATH", str(config_file))
        config = load_config()
        assert config.whoop.base_url == "https://api.whoop.com/v1"


class TestGetApiToken:
    """Tests for get_api_token function."""

    def test_get_token_success(self, monkeypatch):
        """Test getting API token from environment."""
        monkeypatch.setenv("WHOOP_API_TOKEN", "test_token_123")
        token = get_api_token()
        assert token == "test_token_123"

    def test_get_token_missing_raises_error(self, monkeypatch, tmp_path):
        """Test that missing token raises error."""
        monkeypatch.delenv("WHOOP_API_TOKEN", raising=False)
        monkeypatch.chdir(tmp_path)  # Change to temp dir where .whoop_api_token doesn't exist
        with pytest.raises(ConfigValidationError, match="WHOOP_API_TOKEN"):
            get_api_token()

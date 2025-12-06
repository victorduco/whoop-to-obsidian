"""Configuration loading and validation."""

import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from .exceptions import ConfigValidationError
from .models import Config


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load and validate configuration from YAML file.

    Args:
        config_path: Optional path to config file. If not provided, uses
                    WHOOP_CONFIG_PATH environment variable or defaults to
                    'config.yaml' in project root.

    Returns:
        Validated Config object.

    Raises:
        ConfigValidationError: If config file is missing or validation fails.
    """
    # Determine config file path
    if config_path is None:
        config_path = os.environ.get("WHOOP_CONFIG_PATH", "config.yaml")

    config_file = Path(config_path)

    # Check if config file exists
    if not config_file.exists():
        raise ConfigValidationError(
            f"Configuration file not found: {config_file.absolute()}\n"
            "Please create a config.yaml file or set WHOOP_CONFIG_PATH environment variable."
        )

    # Load YAML
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"Failed to parse YAML configuration: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Failed to read configuration file: {e}")

    # Validate with Pydantic
    try:
        config = Config(**config_data)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"  {field}: {message}")

        raise ConfigValidationError(
            "Configuration validation failed:\n" + "\n".join(error_messages)
        )

    return config


def get_api_token() -> str:
    """
    Get Whoop API token from environment variable.

    Returns:
        API token string.

    Raises:
        ConfigValidationError: If WHOOP_API_TOKEN environment variable is not set.
    """
    token = os.environ.get("WHOOP_API_TOKEN")
    if not token:
        raise ConfigValidationError(
            "WHOOP_API_TOKEN environment variable is not set.\n"
            "Please export WHOOP_API_TOKEN with your Whoop API bearer token."
        )
    return token

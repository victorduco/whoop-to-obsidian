"""Custom exception hierarchy for Whoop to Obsidian application."""


class WhoopObsidianError(Exception):
    """Base exception for all Whoop to Obsidian errors."""

    pass


class ConfigValidationError(WhoopObsidianError):
    """Raised when configuration validation fails."""

    pass


class WhoopAPIError(WhoopObsidianError):
    """Raised when Whoop API request fails."""

    pass


class VaultNotFoundError(WhoopObsidianError):
    """Raised when Obsidian vault path is not found."""

    pass


class TableFormatError(WhoopObsidianError):
    """Raised when markdown table parsing or formatting fails."""

    pass


class DuplicateEntryError(WhoopObsidianError):
    """Raised when attempting to create a duplicate entry."""

    pass

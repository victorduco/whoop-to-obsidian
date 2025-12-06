# Whoop to Obsidian

A Python tool to automatically sync health metrics from Whoop API to your Obsidian vault as monthly markdown tables.

## Features

- Fetches daily health metrics from Whoop API (sleep score, recovery, strain, HRV, etc.)
- Creates and updates monthly markdown files in your Obsidian vault
- Configurable table structure and metrics
- Automatic scheduling via macOS launchd
- Duplicate entry detection
- Comprehensive logging with rotation
- Type-safe configuration with validation

## Requirements

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Whoop account with API access
- Obsidian vault

## Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/whoop-to-obsidian.git
   cd whoop-to-obsidian
   ```

3. **Install dependencies using uv**:
   ```bash
   uv sync
   ```

   This will:
   - Create a `.venv` virtual environment automatically
   - Install all dependencies from `uv.lock`
   - Install the package in editable mode

4. **Create configuration file**:
   ```bash
   cp config.example.yaml config.yaml
   ```

5. **Edit config.yaml**:
   - Set `obsidian.vault_path` to your Obsidian vault directory (absolute path)
   - Customize metrics, table structure, and other settings as needed

6. **Set Whoop API token**:
   ```bash
   export WHOOP_API_TOKEN="your_whoop_api_token_here"
   ```

   Add this to your shell profile (~/.zshrc or ~/.bashrc) to persist:
   ```bash
   echo 'export WHOOP_API_TOKEN="your_token"' >> ~/.zshrc
   ```

## Usage

### Manual Sync

Run a one-time sync:

```bash
uv run python -m whoop_obsidian
```

Or activate the environment first:

```bash
source .venv/bin/activate
python -m whoop_obsidian
```

Dry run (test without writing):

```bash
uv run python -m whoop_obsidian --dry-run
```

Use custom config file:

```bash
uv run python -m whoop_obsidian --config /path/to/custom.yaml
```

### Output

The tool creates monthly files in your vault like:

```markdown
# Health Metrics - December 2025

| Date | Sleep Score | Sleep (hrs) | Recovery | Strain | HRV | Notes |
|------|-------------|-------------|----------|--------|-----|-------|
| 12/01 | 85 | 7.5 | 72 | 12.3 | 65 | |
| 12/02 | 78 | 6.8 | 68 | 14.1 | 58 | Added evening workout |
```

## Configuration

See [config.example.yaml](config.example.yaml) for full configuration options.

Key settings:

- **whoop.metrics**: List of metrics to fetch
- **obsidian.vault_path**: Absolute path to your Obsidian vault
- **obsidian.file_prefix**: Prefix for monthly files (e.g., "health")
- **table.columns**: Define table structure and column order
- **execution.deduplication**: Prevent duplicate entries (default: true)
- **logging.level**: Set logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Development

Development dependencies are automatically installed with `uv sync` (defined in `[tool.uv]` section).

Run tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=whoop_obsidian --cov-report=html
```

Add a new dependency:

```bash
uv add package-name
```

Add a development dependency:

```bash
uv add --dev package-name
```

## Project Structure

```
whoop-to-obsidian/
├── whoop_obsidian/           # Main package
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── config.py             # Configuration loading
│   ├── whoop_client.py       # Whoop API client
│   ├── obsidian_writer.py    # Markdown file operations
│   ├── template_generator.py # Template generation
│   ├── models.py             # Pydantic data models
│   └── exceptions.py         # Custom exceptions
├── tests/                    # Test suite
├── logs/                     # Log files (gitignored)
├── config.yaml               # Your config (gitignored)
├── config.example.yaml       # Example configuration
├── pyproject.toml            # Dependencies
└── README.md
```

## Troubleshooting

### Configuration Error

If you see "Configuration file not found":
- Ensure `config.yaml` exists in the project root
- Or set `WHOOP_CONFIG_PATH` environment variable

### Vault Not Found

If you see "Obsidian vault not found":
- Check that `obsidian.vault_path` in config.yaml is an absolute path
- Verify the directory exists

### API Authentication Failed

If you see "Authentication failed":
- Verify your `WHOOP_API_TOKEN` is correctly set
- Check that the token is valid and not expired

### Duplicate Entry

If you see "Entry already exists":
- This is normal if you run the tool multiple times per day
- Disable deduplication in config if you want to allow duplicates

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.

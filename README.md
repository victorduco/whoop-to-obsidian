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
- **Whoop account** with API access (see setup below)
- Obsidian vault

## Getting Whoop API Access

This tool includes a built-in OAuth 2.0 helper to make authentication easy:

### Quick Start (Recommended)

Run the authentication helper:

```bash
uv run python -m whoop_obsidian.auth_helper
```

This will:

1. Open your browser for Whoop authentication
2. Handle the OAuth 2.0 flow automatically
3. Display your access token
4. Show you how to export it as `WHOOP_API_TOKEN`

### Manual Setup

If you prefer to set up OAuth manually:

1. **Create a Developer Account**

   - Visit [WHOOP for Developers](https://developer.whoop.com/)
   - Sign in with your Whoop account
   - Navigate to the Developer Dashboard

2. **Create an Application**

   - Create a new application in the dashboard
   - Set redirect URI to: `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

3. **Get Your Access Token**

   ```bash
   uv run python -m whoop_obsidian.auth_helper \
     --client-id YOUR_CLIENT_ID \
     --client-secret YOUR_CLIENT_SECRET
   ```

4. **Set the Token**

   ```bash
   export WHOOP_API_TOKEN="your_access_token_here"
   ```

   Or save permanently:

   ```bash
   echo 'export WHOOP_API_TOKEN="your_token"' >> ~/.zshrc
   source ~/.zshrc
   ```

For more details, see the [WHOOP API Documentation](https://developer.whoop.com/docs/developing/getting-started/).

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

   This will install all dependencies from `uv.lock` and set up the package in editable mode.

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

### Automatic Scheduling (Recommended)

Set up automatic daily sync at the time specified in your config.yaml:

```bash
./install_scheduler.sh
```

This will:

- Create a launchd service that runs daily at the configured time
- Set up logging to `logs/scheduler.log`

**Scheduler Management:**

Check scheduler status:

```bash
uv run python update_schedule.py status
```

Update schedule after changing config.yaml:

```bash
uv run python update_schedule.py install
```

Remove scheduler:

```bash
uv run python update_schedule.py uninstall
```

The sync time is configured in `config.yaml` under `schedule.run_time` (24-hour format):

```yaml
schedule:
  run_time: "11:00" # Runs daily at 11:00 AM
```

### Manual Sync

Run a one-time sync:

```bash
uv run python -m whoop_obsidian
```

Or use the wrapper script:

```bash
./sync_whoop.sh
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

| Date  | Sleep Score | Sleep (hrs) | Recovery | Strain | HRV | Notes                 |
| ----- | ----------- | ----------- | -------- | ------ | --- | --------------------- |
| 12/01 | 85          | 7.5         | 72       | 12.3   | 65  |                       |
| 12/02 | 78          | 6.8         | 68       | 14.1   | 58  | Added evening workout |
```

## Configuration

See [config.example.yaml](config.example.yaml) for full configuration options.

Key settings:

- **whoop.metrics**: List of metrics to fetch
- **obsidian.vault_path**: Absolute path to your Obsidian vault
- **obsidian.file_prefix**: Prefix for monthly files (e.g., "health")
- **table.columns**: Define table structure and column order
- **schedule.run_time**: Time to run daily sync (HH:MM, 24-hour format)
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
├── sync_whoop.sh             # Wrapper script for scheduled runs
├── update_schedule.py        # Scheduler management script
├── install_scheduler.sh      # Scheduler installation script
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

### Scheduler Not Running

If automatic sync is not working:

- Check scheduler status: `python update_schedule.py status`
- View scheduler logs: `cat logs/scheduler.log`
- Reinstall scheduler: `./install_scheduler.sh`
- Verify time in config.yaml is correct

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.

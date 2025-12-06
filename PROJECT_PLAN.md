# Whoop to Obsidian - Project Plan

## Overview
Python application that fetches health metrics from Whoop API and creates/updates monthly markdown files in Obsidian vault. Runs daily at configurable time (default 11:00 AM local time) via macOS launchd scheduler.

All project code, comments, documentation, and naming conventions in English.

## Technology Stack
- **Python**: 3.11+ (minimum version)
- **Package Manager**: uv (see dependencies.txt for package list)
- **Configuration**: YAML with validation on startup
- **Data Format**: JSON for API, Markdown tables for output
- **Scheduler**: macOS launchd (user-level ~/Library/LaunchAgents)
- **Type Safety**: Type hints throughout codebase

## Dependencies
Project dependencies managed via uv:
- `requests` - HTTP client for Whoop API
- `pyyaml` - YAML configuration parsing
- `python-dateutil` - Timezone and date handling
- `pydantic` - Configuration validation and data models

See `pyproject.toml` for complete dependency list.

## Data Collection

### Whoop API Integration
- **API Endpoint**: `https://api.whoop.com/v1` (configurable base URL in config)
- **Authentication**: Bearer token via environment variable `WHOOP_API_TOKEN`
- **Response Format**: JSON
- **Rate Limiting**: Respects 429 responses, exponential backoff (max 3 retries)
- **Timeout**: 30 seconds per request

### Metrics to Fetch
Four distinct metrics from Whoop API:
1. **Sleep Score** - Overall sleep quality score (0-100)
2. **Sleep Duration** - Hours slept (separate column from Sleep Score)
3. **Recovery Score** - Body recovery metric (0-100)
4. **Strain Score** - Daily strain/exertion (0-21)
5. **HRV** - Heart Rate Variability in ms

### Data Validation
Required validation checks:
- All metric values are numeric and within expected ranges
- Response JSON contains required fields
- Timestamp is present and parsable
- Missing metrics logged as WARNING, entry still created with empty cells

## Configuration File

### Location and Loading
- **Path**: `config.yaml` in project root (hardcoded)
- **Fallback**: If missing, exit with error code 1 and error message
- **Validation**: Full schema validation on startup using Pydantic
- **Reload**: Requires script restart for config changes

### Configuration Schema

```yaml
# Whoop API Configuration
whoop:
  base_url: "https://api.whoop.com/v1"  # API endpoint base URL
  metrics:  # List of metrics to fetch (must not be empty)
    - sleep_score
    - sleep_duration
    - recovery_score
    - strain_score
    - hrv
  timeout_seconds: 30

# Obsidian Integration
obsidian:
  vault_path: "/absolute/path/to/vault"  # Must be absolute path
  file_prefix: "health"  # No special chars allowed (validated: alphanumeric, dash, underscore)

# Table Structure
table:
  date_format: "MM/DD"  # Format for date column
  columns:  # Column definitions in display order
    - name: "Date"
      type: "date"
    - name: "Sleep Score"
      type: "metric"
      metric_key: "sleep_score"
    - name: "Sleep (hrs)"
      type: "metric"
      metric_key: "sleep_duration"
      decimal_places: 1
    - name: "Recovery"
      type: "metric"
      metric_key: "recovery_score"
    - name: "Strain"
      type: "metric"
      metric_key: "strain_score"
      decimal_places: 1
    - name: "HRV"
      type: "metric"
      metric_key: "hrv"
    - name: "Notes"
      type: "custom"  # Empty for manual entry

  alignment: "left"  # Markdown table alignment: left, center, or right

# Color Thresholds (for future dashboard/reporting features)
# Not rendered in markdown files, stored for potential extensions
thresholds:
  sleep_score:
    green: [85, 100]
    yellow: [70, 84]
    red: [0, 69]
  recovery_score:
    green: [67, 100]
    yellow: [34, 66]
    red: [0, 33]
  strain_score:
    green: [0, 14]
    yellow: [15, 18]
    red: [19, 21]

# Scheduling
schedule:
  run_time: "11:00"  # Time in HH:MM format (24-hour, local timezone)

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/whoop_sync.log"  # Relative to project root
  rotation: true  # Enable log rotation (max 10MB, 5 backups)

# Execution
execution:
  timezone: "local"  # Use system local timezone
  allow_historical: false  # If true, process data even if from previous months
  deduplication: true  # Check for existing date entry before appending
```

## File Management Logic

### File Naming Convention
Monthly files named: `{prefix}-{MonthName}.md`
- **Prefix**: From config (`obsidian.file_prefix`)
- **Month**: Capitalized English month name (e.g., "December")
- **Extension**: `.md` automatically appended
- **Example**: `health-December.md`

### Month Determination
- Uses local system timezone to determine current month
- New file created on first run of each month
- Historical data (previous months) skipped unless `execution.allow_historical: true`

### File Operations Flow
1. **Validate vault path**: Check if `obsidian.vault_path` exists
   - If not found: Log ERROR and exit with code 1
2. **Determine target file**: Build filename from current month
3. **Check file existence**:
   - If exists: Validate markdown table structure
   - If not exists: Create from programmatically generated template
4. **Deduplication check**: If enabled, scan table for today's date
   - If found: Log INFO and skip (no duplicate rows)
   - If not found: Proceed to append
5. **Append row**: Add new row to end of table using atomic write
6. **Verify write**: Confirm file updated successfully

### Atomic Write Strategy
- Read entire file into memory
- Append new row to table structure
- Write to temporary file `.{filename}.tmp`
- Atomic rename to replace original
- No backup files created (rely on Obsidian sync/git)

### Table Structure Validation
If file exists but table structure differs from config:
- Log WARNING with detected vs expected columns
- Attempt append with best-effort column matching
- Developer should manually reconcile structure

## Markdown Template

### Template Generation
Templates are **programmatically generated** from config, not stored as files.

### File Structure
```markdown
# Health Metrics - {Month} {Year}

| Date | Sleep Score | Sleep (hrs) | Recovery | Strain | HRV | Notes |
|------|-------------|-------------|----------|--------|-----|-------|
| 12/01 | 85 | 7.5 | 72 | 12.3 | 65 | |
| 12/02 | 78 | 6.8 | 68 | 14.1 | 58 | Added evening workout |
```

### Table Details
- **Alignment**: Configurable (default: left-aligned)
- **Date Format**: MM/DD from config
- **Metric Formatting**:
  - Integers for scores (no decimals)
  - Configurable decimal places per metric (default: 0)
  - Missing values: empty cell (not "N/A" or "0")
- **Custom Columns**: Empty string placeholder
- **Row Order**: Chronological, new rows appended to end

## Automation

### launchd Configuration
- **Plist Location**: `~/Library/LaunchAgents/com.user.whoop-obsidian.plist`
- **Generation**: Automated via `setup_automation.py` script
- **Installation**: Script generates plist and loads via `launchctl load`

### Setup Script
Separate CLI command for automation setup:
```bash
python -m whoop_obsidian.setup_automation
```

This script:
1. Generates launchd plist from config
2. Writes to `~/Library/LaunchAgents/`
3. Loads plist via `launchctl load`
4. Verifies scheduling with `launchctl list`

### Logging for launchd
- **stdout**: Redirected to `logs/whoop_cron_out.log`
- **stderr**: Redirected to `logs/whoop_cron_err.log`
- Both configured in plist file

### Concurrent Execution Prevention
- Lockfile mechanism: `.whoop_sync.lock` in project root
- Acquired at startup, released on exit
- If lock exists: Log WARNING and exit immediately (exit code 0)

## Project Structure

```
whoop-to-obsidian/
├── whoop_obsidian/           # Main package
│   ├── __init__.py
│   ├── __main__.py           # Entry point: python -m whoop_obsidian
│   ├── config.py             # Configuration loading and validation
│   ├── whoop_client.py       # Whoop API client
│   ├── obsidian_writer.py    # Markdown file operations
│   ├── template_generator.py # Template generation logic
│   ├── models.py             # Pydantic data models
│   ├── exceptions.py         # Custom exception hierarchy
│   └── setup_automation.py   # Automation setup utility
├── tests/                    # Test suite
│   ├── test_config.py
│   ├── test_whoop_client.py
│   ├── test_obsidian_writer.py
│   └── test_integration.py
├── logs/                     # Log files (gitignored)
├── config.yaml               # Configuration file
├── config.example.yaml       # Example configuration
├── pyproject.toml            # uv/pip dependencies
├── README.md                 # Setup and usage instructions
└── .whoop_sync.lock          # Lockfile (gitignored)
```

## Error Handling

### Exception Hierarchy
Custom exceptions for clear error handling:
- `WhoopAPIError` - API request failures
- `ConfigValidationError` - Invalid configuration
- `VaultNotFoundError` - Obsidian vault path missing
- `TableFormatError` - Markdown table parsing issues
- `DuplicateEntryError` - Entry already exists (if dedup enabled)

All inherit from base `WhoopObsidianError`.

### Exit Codes
- `0` - Success or benign skip (e.g., duplicate entry, lock exists)
- `1` - Configuration error or vault not found
- `2` - API authentication failure
- `3` - API request failure (network/timeout)
- `4` - File operation error

### Retry Logic
- **API Requests**: 3 retries with exponential backoff (1s, 2s, 4s)
- **File Operations**: No retries (fail fast)
- **Authentication**: No retry (immediate failure)

### Partial Data Handling
If some metrics missing from API response:
- Log WARNING for each missing metric
- Create entry with empty cells for missing values
- Do NOT skip entire entry

### Logging Strategy
- **Level**: Configurable (default: INFO)
- **Format**: `{timestamp} [{level}] {module}:{line} - {message}`
- **Rotation**: 10MB max size, 5 backup files
- **Location**: `logs/whoop_sync.log`

## Implementation Guidelines

### Code Standards
- **Type Hints**: Required for all functions and methods
- **Docstrings**: Google-style for all public APIs
- **Data Models**: Pydantic dataclasses for API responses and config
- **Error Messages**: Clear, actionable English messages
- **Synchronous**: All operations synchronous (no async/await)

### Environment Variables
- `WHOOP_API_TOKEN` - Required, Whoop API bearer token
- `WHOOP_CONFIG_PATH` - Optional, override config.yaml path

### Development Setup
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Create virtual environment: `uv venv`
3. Install dependencies: `uv pip install -e ".[dev]"`
4. Copy config: `cp config.example.yaml config.yaml`
5. Set environment variable: `export WHOOP_API_TOKEN="your_token"`

### Testing Strategy
- **Unit Tests**: Each module tested independently
- **Integration Tests**: Full flow with mocked API
- **Config Validation Tests**: All validation rules covered
- **Test Framework**: pytest
- **Coverage Target**: >80%

### CLI Interface
Manual execution supported via:
```bash
python -m whoop_obsidian          # Run sync
python -m whoop_obsidian --config custom.yaml  # Custom config
python -m whoop_obsidian --dry-run  # Simulate without writing
```

## Implementation Notes

### Key Design Decisions
- **Append-Only**: Never modify or delete existing rows
- **Local Timezone**: All times in system local timezone, not UTC
- **Deduplication**: Based on date string match in table
- **No Backups**: Rely on Obsidian sync or git for version control
- **Programmatic Templates**: No template files, generated from config
- **Environment Secrets**: API token via environment variable only
- **Synchronous**: Simple synchronous execution, no async complexity
- **User-Level Automation**: launchd plist in user directory, not system

### Future Extensibility
- Color thresholds stored in config for future dashboard features
- Modular design allows adding new metric sources
- Template system can be extended for custom formatting

### Locale Handling
- Force English for all date/month names regardless of system locale
- Use `locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')` at startup

## Security Considerations
- API token never stored in config.yaml or git
- Config validation prevents path traversal attacks
- File operations restricted to vault directory
- No shell command execution from user input

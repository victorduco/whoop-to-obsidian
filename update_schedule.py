#!/usr/bin/env python3
"""
Update schedule script for Whoop to Obsidian sync.
Reads the schedule from config.yaml and updates the launchd plist file.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is not installed", file=sys.stderr)
    print("Please run: uv add pyyaml", file=sys.stderr)
    sys.exit(1)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent


def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = get_project_root() / "config.yaml"
    
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)


def parse_time(time_str: str) -> tuple[int, int]:
    """
    Parse time string in HH:MM format.
    
    Args:
        time_str: Time in HH:MM format (24-hour)
    
    Returns:
        Tuple of (hour, minute)
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time range")
        return hour, minute
    except Exception as e:
        print(f"Error parsing time '{time_str}': {e}", file=sys.stderr)
        print("Time must be in HH:MM format (24-hour)", file=sys.stderr)
        sys.exit(1)


def create_plist(hour: int, minute: int, project_root: Path) -> str:
    """
    Create launchd plist content.
    
    Args:
        hour: Hour to run (0-23)
        minute: Minute to run (0-59)
        project_root: Path to project root directory
    
    Returns:
        Plist XML content as string
    """
    label = "com.whoop.obsidian.sync"
    script_path = project_root / "sync_whoop.sh"
    log_path = project_root / "logs" / "scheduler.log"
    error_log_path = project_root / "logs" / "scheduler_error.log"
    
    # Ensure logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{script_path}</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>{project_root}</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    
    <key>StandardErrorPath</key>
    <string>{error_log_path}</string>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""
    return plist_content


def get_plist_path() -> Path:
    """Get the path where the plist should be installed."""
    home = Path.home()
    return home / "Library" / "LaunchAgents" / "com.whoop.obsidian.sync.plist"


def update_schedule(unload_first: bool = True) -> None:
    """
    Update the schedule from config.yaml.
    
    Args:
        unload_first: If True, unload existing schedule before updating
    """
    # Load config and get schedule time
    config = load_config()
    
    if 'schedule' not in config or 'run_time' not in config['schedule']:
        print("Error: 'schedule.run_time' not found in config.yaml", file=sys.stderr)
        sys.exit(1)
    
    run_time = config['schedule']['run_time']
    hour, minute = parse_time(run_time)
    
    # Get paths
    project_root = get_project_root()
    plist_path = get_plist_path()
    
    # Ensure LaunchAgents directory exists
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Unload existing schedule if requested and if it exists
    if unload_first and plist_path.exists():
        print(f"Unloading existing schedule...")
        try:
            subprocess.run(
                ['launchctl', 'unload', str(plist_path)],
                check=False,  # Don't fail if not loaded
                capture_output=True
            )
        except Exception as e:
            print(f"Warning: Could not unload existing schedule: {e}", file=sys.stderr)
    
    # Create and write new plist
    plist_content = create_plist(hour, minute, project_root)
    
    try:
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        print(f"✓ Plist file written to: {plist_path}")
    except Exception as e:
        print(f"Error writing plist file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Load the schedule
    print(f"Loading schedule to run daily at {run_time}...")
    try:
        result = subprocess.run(
            ['launchctl', 'load', str(plist_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Schedule loaded successfully")
        print(f"  Sync will run daily at {hour:02d}:{minute:02d}")
    except subprocess.CalledProcessError as e:
        print(f"Error loading schedule: {e}", file=sys.stderr)
        if e.stderr:
            print(f"Details: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def unload_schedule() -> None:
    """Unload and remove the schedule."""
    plist_path = get_plist_path()
    
    if not plist_path.exists():
        print("No schedule is currently installed")
        return
    
    print(f"Unloading schedule...")
    try:
        subprocess.run(
            ['launchctl', 'unload', str(plist_path)],
            check=False,
            capture_output=True
        )
    except Exception as e:
        print(f"Warning: Could not unload schedule: {e}", file=sys.stderr)
    
    # Remove plist file
    try:
        plist_path.unlink()
        print(f"✓ Schedule removed")
    except Exception as e:
        print(f"Error removing plist file: {e}", file=sys.stderr)
        sys.exit(1)


def check_schedule() -> None:
    """Check if schedule is installed and show current configuration."""
    plist_path = get_plist_path()
    
    if not plist_path.exists():
        print("Schedule is not currently installed")
        print(f"Run 'python update_schedule.py install' to set it up")
        return
    
    # Try to get status from launchctl
    try:
        result = subprocess.run(
            ['launchctl', 'list', 'com.whoop.obsidian.sync'],
            check=False,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Schedule is installed and loaded")
        else:
            print("⚠ Schedule file exists but is not loaded")
            print("  Run 'python update_schedule.py install' to load it")
    except Exception as e:
        print(f"Could not check status: {e}", file=sys.stderr)
    
    # Show configured time from config
    try:
        config = load_config()
        run_time = config.get('schedule', {}).get('run_time', 'unknown')
        print(f"  Configured time: {run_time}")
    except:
        pass


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'install':
            update_schedule(unload_first=True)
        elif command == 'uninstall':
            unload_schedule()
        elif command == 'status':
            check_schedule()
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            print("Usage: python update_schedule.py [install|uninstall|status]", file=sys.stderr)
            sys.exit(1)
    else:
        # Default: update/install schedule
        update_schedule(unload_first=True)


if __name__ == '__main__':
    main()

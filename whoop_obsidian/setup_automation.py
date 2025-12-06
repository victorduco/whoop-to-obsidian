"""Setup automation using macOS launchd."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .config import load_config


PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.whoop-obsidian</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>-m</string>
        <string>whoop_obsidian</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{working_directory}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>WHOOP_API_TOKEN</key>
        <string>{api_token}</string>
        <key>WHOOP_CONFIG_PATH</key>
        <string>{config_path}</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{stdout_log}</string>
    <key>StandardErrorPath</key>
    <string>{stderr_log}</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""


def get_python_path() -> str:
    """
    Get path to Python interpreter.

    Returns:
        Absolute path to Python executable.
    """
    return sys.executable


def get_launch_agents_dir() -> Path:
    """
    Get path to user's LaunchAgents directory.

    Returns:
        Path to ~/Library/LaunchAgents
    """
    home = Path.home()
    launch_agents = home / "Library" / "LaunchAgents"

    # Ensure directory exists
    launch_agents.mkdir(parents=True, exist_ok=True)

    return launch_agents


def generate_plist(
    config_path: Optional[str] = None,
) -> str:
    """
    Generate launchd plist content.

    Args:
        config_path: Optional path to config file.

    Returns:
        Plist XML content as string.

    Raises:
        SystemExit: If required environment variables are missing.
    """
    # Load configuration
    config = load_config(config_path)

    # Get API token
    api_token = os.environ.get("WHOOP_API_TOKEN", "")
    if not api_token:
        print("Error: WHOOP_API_TOKEN environment variable not set", file=sys.stderr)
        print("Please set it with: export WHOOP_API_TOKEN='your_token'", file=sys.stderr)
        sys.exit(1)

    # Parse run time
    hour, minute = config.schedule.run_time.split(":")

    # Get paths
    python_path = get_python_path()
    working_directory = Path.cwd().absolute()

    # Resolve config path
    if config_path:
        resolved_config_path = Path(config_path).absolute()
    else:
        resolved_config_path = working_directory / "config.yaml"

    # Log paths
    logs_dir = working_directory / "logs"
    logs_dir.mkdir(exist_ok=True)
    stdout_log = logs_dir / "whoop_cron_out.log"
    stderr_log = logs_dir / "whoop_cron_err.log"

    # Generate plist
    plist_content = PLIST_TEMPLATE.format(
        python_path=python_path,
        working_directory=working_directory,
        api_token=api_token,
        config_path=resolved_config_path,
        hour=hour,
        minute=minute,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
    )

    return plist_content


def install_plist(plist_content: str) -> Path:
    """
    Install plist to LaunchAgents directory.

    Args:
        plist_content: Plist XML content.

    Returns:
        Path to installed plist file.
    """
    launch_agents_dir = get_launch_agents_dir()
    plist_path = launch_agents_dir / "com.user.whoop-obsidian.plist"

    # Write plist file
    plist_path.write_text(plist_content, encoding="utf-8")
    print(f"✓ Plist file written to: {plist_path}")

    return plist_path


def load_plist(plist_path: Path) -> bool:
    """
    Load plist using launchctl.

    Args:
        plist_path: Path to plist file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Unload existing plist if it exists
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
            check=False,  # Don't error if not loaded
        )

        # Load new plist
        result = subprocess.run(
            ["launchctl", "load", str(plist_path)],
            capture_output=True,
            text=True,
            check=True,
        )

        print(f"✓ Plist loaded successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error loading plist: {e.stderr}", file=sys.stderr)
        return False


def verify_installation() -> bool:
    """
    Verify that the plist is loaded.

    Returns:
        True if loaded, False otherwise.
    """
    try:
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
            check=True,
        )

        if "com.user.whoop-obsidian" in result.stdout:
            print("✓ Service verified in launchctl list")
            return True
        else:
            print("⚠ Service not found in launchctl list", file=sys.stderr)
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error verifying installation: {e.stderr}", file=sys.stderr)
        return False


def uninstall() -> bool:
    """
    Uninstall the launchd automation.

    Returns:
        True if successful, False otherwise.
    """
    launch_agents_dir = get_launch_agents_dir()
    plist_path = launch_agents_dir / "com.user.whoop-obsidian.plist"

    if not plist_path.exists():
        print("Automation is not installed")
        return True

    try:
        # Unload plist
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
            check=False,
        )

        # Remove plist file
        plist_path.unlink()
        print(f"✓ Automation uninstalled successfully")
        return True

    except Exception as e:
        print(f"Error uninstalling: {e}", file=sys.stderr)
        return False


def main() -> int:
    """
    Main entry point for setup automation script.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup automated Whoop to Obsidian sync using launchd"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall the automation",
    )

    args = parser.parse_args()

    if args.uninstall:
        success = uninstall()
        return 0 if success else 1

    print("Setting up Whoop to Obsidian automation...\n")

    try:
        # Generate plist
        print("Generating launchd plist...")
        plist_content = generate_plist(args.config)

        # Install plist
        plist_path = install_plist(plist_content)

        # Load plist
        print("\nLoading plist with launchctl...")
        if not load_plist(plist_path):
            return 1

        # Verify installation
        print("\nVerifying installation...")
        if not verify_installation():
            print("\n⚠ Installation may not be complete", file=sys.stderr)
            return 1

        print("\n✓ Automation setup complete!")
        print(f"\nThe sync will run daily at the configured time.")
        print(f"Logs will be written to:")
        print(f"  - {Path.cwd() / 'logs' / 'whoop_cron_out.log'}")
        print(f"  - {Path.cwd() / 'logs' / 'whoop_cron_err.log'}")
        print(f"\nTo uninstall, run: python -m whoop_obsidian.setup_automation --uninstall")

        return 0

    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        return 1
    except Exception as e:
        print(f"\nError during setup: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

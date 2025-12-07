"""CLI helper for Whoop OAuth 2.0 authentication."""

import argparse
import json
import os
import sys
from pathlib import Path

from .oauth import interactive_auth


def main():
    """Main entry point for auth helper."""
    parser = argparse.ArgumentParser(
        description="Whoop OAuth 2.0 Authentication Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive authentication (opens browser)
  python -m whoop_obsidian.auth_helper

  # Save token to file
  python -m whoop_obsidian.auth_helper --save-token ~/.whoop_token.json

  # Use custom credentials
  python -m whoop_obsidian.auth_helper --client-id YOUR_ID --client-secret YOUR_SECRET
        """,
    )

    parser.add_argument(
        "--client-id",
        type=str,
        help="OAuth client ID (default: uses built-in credentials)",
    )
    parser.add_argument(
        "--client-secret",
        type=str,
        help="OAuth client secret (default: uses built-in credentials)",
    )
    parser.add_argument(
        "--save-token",
        type=str,
        metavar="FILE",
        help="Save access token to file (JSON format)",
    )

    args = parser.parse_args()

    # Get credentials from environment variables or command line
    client_id = args.client_id or os.environ.get("WHOOP_CLIENT_ID")
    client_secret = args.client_secret or os.environ.get("WHOOP_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Error: OAuth credentials not provided.", file=sys.stderr)
        print("\nPlease provide credentials via:", file=sys.stderr)
        print("  1. Command line: --client-id YOUR_ID --client-secret YOUR_SECRET", file=sys.stderr)
        print("  2. Environment variables: WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET", file=sys.stderr)
        return 1

    try:
        # Perform OAuth flow
        token_data = interactive_auth(client_id, client_secret)

        # Display token information
        print("\nToken Information:")
        print("-" * 70)
        print(f"Access Token:  {token_data['access_token'][:50]}...")
        print(f"Token Type:    {token_data.get('token_type', 'Bearer')}")
        print(f"Expires In:    {token_data.get('expires_in', 'N/A')} seconds")

        if "refresh_token" in token_data:
            print(f"Refresh Token: {token_data['refresh_token'][:50]}...")

        print("-" * 70)

        # Show how to use the token
        print("\nTo use this token, add it to your environment:")
        print(f"\n  export WHOOP_API_TOKEN='{token_data['access_token']}'")
        print("\nOr add to your shell profile (~/.zshrc or ~/.bashrc):")
        print(f"\n  echo 'export WHOOP_API_TOKEN=\"{token_data['access_token']}\"' >> ~/.zshrc")
        # Сохраняем токен в .whoop_api_token
        try:
            with open(".whoop_api_token", "w", encoding="utf-8") as f:
                f.write(token_data['access_token'].strip() + "\n")
            print("\n✓ Token saved to .whoop_api_token\n")
        except Exception as e:
            print(f"\n⚠ Could not save token to .whoop_api_token: {e}\n")

        # Save to file if requested
        if args.save_token:
            token_file = Path(args.save_token).expanduser()
            with open(token_file, "w") as f:
                json.dump(token_data, f, indent=2)
            print(f"\n✓ Token saved to: {token_file}")
            print(f"\nTo load the token from file:")
            print(f"  export WHOOP_API_TOKEN=$(cat {token_file} | jq -r .access_token)")

        print("\n" + "=" * 70)
        print("Authentication complete!")
        print("=" * 70 + "\n")

        return 0

    except KeyboardInterrupt:
        print("\n\nAuthentication cancelled by user")
        return 1
    except Exception as e:
        print(f"\n\nError during authentication: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

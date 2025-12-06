"""CLI helper for Whoop OAuth 2.0 authentication."""

import argparse
import json
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

    # Default credentials (you can change these)
    client_id = args.client_id or "8b1dd617-41e6-4e3a-bca3-9a9c072460de"
    client_secret = (
        args.client_secret
        or "d221daaa4edeede3bab128edf65a5e72816a4c1ed9ab48cda4421127c70fb646"
    )

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

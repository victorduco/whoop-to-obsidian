"""OAuth 2.0 authentication for Whoop API."""

import http.server
import logging
import secrets
import socketserver
import urllib.parse
import webbrowser
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests

logger = logging.getLogger(__name__)


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    authorization_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        # Parse query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)

        if "code" in params:
            OAuthCallbackHandler.authorization_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <body>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """
            )
        elif "error" in params:
            OAuthCallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
                <html>
                <body>
                <h1>Authentication Failed</h1>
                <p>Error: {params.get('error_description', ['Unknown error'])[0]}</p>
                </body>
                </html>
                """.encode()
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid callback")

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class WhoopOAuth:
    """Whoop OAuth 2.0 client."""

    AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
    TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
    REDIRECT_URI = "http://localhost:8000/callback"

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize OAuth client.

        Args:
            client_id: OAuth client ID.
            client_secret: OAuth client secret.
        """
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Generate OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection.

        Returns:
            Tuple of (authorization_url, state)
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.REDIRECT_URI,
            "scope": "read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement",
            "state": state,
        }

        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"
        return auth_url, state

    def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback.

        Returns:
            Token response dictionary with access_token, refresh_token, etc.

        Raises:
            Exception: If token exchange fails.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.REDIRECT_URI,
        }

        try:
            response = requests.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for token: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            raise

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from previous authorization.

        Returns:
            New token response dictionary.

        Raises:
            Exception: If token refresh fails.
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh token: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            raise

    def authorize_interactive(self) -> dict:
        """
        Perform interactive OAuth flow (opens browser).

        Returns:
            Token response dictionary.

        Raises:
            Exception: If authorization fails.
        """
        # Generate authorization URL
        auth_url, state = self.get_authorization_url()

        print("\n" + "=" * 70)
        print("WHOOP OAuth 2.0 Authorization")
        print("=" * 70)
        print("\nOpening browser for authorization...")
        print(f"If browser doesn't open, visit: {auth_url}\n")

        # Open browser
        webbrowser.open(auth_url)

        # Start local server to receive callback
        print("Waiting for authorization callback...")
        print("(Server running on http://localhost:8000)")
        print("-" * 70)

        # Reset handler state
        OAuthCallbackHandler.authorization_code = None
        OAuthCallbackHandler.error = None

        # Start server
        with socketserver.TCPServer(("localhost", 8000), OAuthCallbackHandler) as httpd:
            # Handle single request (the callback)
            httpd.handle_request()

        # Check for errors
        if OAuthCallbackHandler.error:
            raise Exception(f"Authorization failed: {OAuthCallbackHandler.error}")

        if not OAuthCallbackHandler.authorization_code:
            raise Exception("No authorization code received")

        print("\n✓ Authorization code received")
        print("Exchanging code for access token...")

        # Exchange code for token
        token_data = self.exchange_code_for_token(
            OAuthCallbackHandler.authorization_code
        )

        print("✓ Access token obtained successfully!")
        print("=" * 70 + "\n")

        return token_data


def interactive_auth(client_id: str, client_secret: str) -> dict:
    """
    Convenience function for interactive OAuth flow.

    Args:
        client_id: OAuth client ID.
        client_secret: OAuth client secret.

    Returns:
        Token response dictionary with access_token, refresh_token, etc.
    """
    oauth = WhoopOAuth(client_id, client_secret)
    return oauth.authorize_interactive()

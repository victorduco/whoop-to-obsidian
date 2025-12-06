#!/bin/bash
# Helper script to get Whoop OAuth token

echo "Starting OAuth authentication..."
echo ""
echo "This will:"
echo "  1. Open your browser"
echo "  2. Ask you to login to Whoop"
echo "  3. Get your access token"
echo ""
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Run the auth helper
uv run python -m whoop_obsidian.auth_helper --save-token ~/.whoop_token.json

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Token saved to ~/.whoop_token.json"
    echo ""
    echo "To use the token, run:"
    echo "  export WHOOP_API_TOKEN=\$(cat ~/.whoop_token.json | python3 -c 'import sys, json; print(json.load(sys.stdin)[\"access_token\"])')"
    echo ""
    echo "Or add to your shell profile:"
    echo "  echo 'export WHOOP_API_TOKEN=\"'\$(cat ~/.whoop_token.json | python3 -c 'import sys, json; print(json.load(sys.stdin)[\"access_token\"])')\"' >> ~/.zshrc"
else
    echo ""
    echo "❌ Authentication failed"
    echo "Please check the error messages above"
fi

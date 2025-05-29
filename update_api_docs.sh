#!/bin/bash
# Script to generate API documentation and update the site
# Usage: ./update_api_docs.sh [commit_message]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMIT_MESSAGE=${1:-"Update API documentation"}

echo "Generating API documentation..."
"$SCRIPT_DIR/docs_create/generate_api_docs.py"

echo "Previewing the documentation..."
echo "Starting mkdocs server. Press Ctrl+C when done reviewing."
echo "Documentation will be available at http://127.0.0.1:8000/"
mkdocs serve &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Open browser if available
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://127.0.0.1:8000/api/
elif command -v open >/dev/null 2>&1; then
    open http://127.0.0.1:8000/api/
fi

# Wait for user to review
read -p "Press Enter to stop the server and continue with deployment..."

# Kill the server
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

# Ask user if they want to deploy
read -p "Deploy the updated documentation to GitHub Pages? (y/n): " DEPLOY_DOCS

if [[ "$DEPLOY_DOCS" =~ ^[Yy] ]]; then
    echo "Deploying documentation..."
    "$SCRIPT_DIR/docs_create/push_site_to_ghpages.sh" "$COMMIT_MESSAGE"
    echo "Documentation deployed!"
else
    echo "Documentation updated but not deployed."
    echo "To deploy later, run: ./docs_create/push_site_to_ghpages.sh \"$COMMIT_MESSAGE\""
fi

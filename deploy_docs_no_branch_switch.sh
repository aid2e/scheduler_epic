#!/bin/bash
# Wrapper script for push_site_to_ghpages.sh
# Usage: ./deploy_docs_no_branch_switch.sh [commit_message]

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default commit message
COMMIT_MESSAGE=${1:-"Update documentation"}

# Run the actual script
"$SCRIPT_DIR/docs_create/push_site_to_ghpages.sh" "$COMMIT_MESSAGE"

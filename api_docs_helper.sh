#!/bin/bash
# Script to generate and manage API documentation
# Usage: ./api_docs_helper.sh [command]
#
# Commands:
#   generate  - Generate API documentation only
#   preview   - Generate and preview documentation
#   deploy    - Generate, preview, and deploy documentation
#   validate  - Check docstrings in the codebase
#   clean     - Remove generated API documentation
#   help      - Show this help message

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMAND=${1:-"help"}
COMMIT_MESSAGE=${2:-"Update API documentation"}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to generate API documentation
generate_docs() {
  echo -e "${BLUE}Generating API documentation...${NC}"
  "$SCRIPT_DIR/docs_create/generate_api_docs.py"
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API documentation generated in docs/api/${NC}"
  else
    echo -e "${RED}✗ API documentation generation failed${NC}"
    exit 1
  fi
}

# Function to preview documentation
preview_docs() {
  echo -e "${BLUE}Starting documentation preview server...${NC}"
  echo "Documentation will be available at http://127.0.0.1:8000/"
  echo "Press Ctrl+C to stop the server when done."
  mkdocs serve
}

# Function to deploy documentation
deploy_docs() {
  echo -e "${BLUE}Deploying documentation with message: '${COMMIT_MESSAGE}'${NC}"
  "$SCRIPT_DIR/docs_create/push_site_to_ghpages.sh" "$COMMIT_MESSAGE"
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Documentation deployed to GitHub Pages${NC}"
  else
    echo -e "${RED}✗ Documentation deployment failed${NC}"
    exit 1
  fi
}

# Function to validate docstrings
validate_docstrings() {
  echo -e "${BLUE}Validating docstrings in the codebase...${NC}"
  
  # Use the Python docstring checker script
  "$SCRIPT_DIR/docs_create/check_docstrings.py" "$SCRIPT_DIR/scheduler"
  
  # Check the exit code
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docstring validation passed${NC}"
  else
    echo -e "${YELLOW}⚠️ Some docstrings need improvement${NC}"
    echo "Run './api_docs_helper.sh generate' to create documentation anyway."
  fi
}

# Function to clean generated documentation
clean_docs() {
  echo -e "${BLUE}Cleaning generated API documentation...${NC}"
  find "$SCRIPT_DIR/docs/api" -name "*.md" -delete
  echo -e "${GREEN}✓ API documentation cleaned${NC}"
}

# Help message
show_help() {
  echo -e "${BLUE}API Documentation Helper${NC}"
  echo "========================"
  echo
  echo "This script helps manage API documentation for your project."
  echo
  echo "Usage: ./api_docs_helper.sh [command] [commit_message]"
  echo
  echo "Commands:"
  echo "  generate  - Generate API documentation only"
  echo "  preview   - Generate and preview documentation"
  echo "  deploy    - Generate, preview, and deploy documentation"
  echo "  validate  - Check docstrings in the codebase"
  echo "  clean     - Remove generated API documentation"
  echo "  help      - Show this help message"
  echo
  echo "Examples:"
  echo "  ./api_docs_helper.sh generate"
  echo "  ./api_docs_helper.sh deploy \"Updated method documentation\""
  echo
  echo "For more information, see docs/api_documentation.md"
}

# Main logic
case "$COMMAND" in
  generate)
    generate_docs
    ;;
  preview)
    generate_docs
    preview_docs
    ;;
  deploy)
    generate_docs
    echo "Previewing documentation before deployment..."
    echo -e "${YELLOW}Starting preview server. Press Ctrl+C when ready to deploy.${NC}"
    
    # Start server with a timeout
    timeout 30s mkdocs serve || true
    
    read -p "Deploy documentation to GitHub Pages? (y/n): " CONFIRM
    if [[ "$CONFIRM" =~ ^[Yy] ]]; then
      deploy_docs
    else
      echo "Deployment cancelled."
    fi
    ;;
  validate)
    validate_docstrings
    ;;
  clean)
    clean_docs
    ;;
  help|*)
    show_help
    ;;
esac

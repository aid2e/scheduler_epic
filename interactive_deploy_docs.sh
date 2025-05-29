#!/bin/bash
# Interactive script to help users choose the right deployment option for GitHub Pages
# This script guides users through deploying MkDocs documentation to GitHub Pages

set -e

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}  MkDocs GitHub Pages Deployment  ${NC}"
echo -e "${BLUE}==================================${NC}"
echo

# Check for uncommitted changes
HAS_CHANGES=false
if [[ -n $(git status -s) ]]; then
  HAS_CHANGES=true
  echo -e "${YELLOW}⚠️  You have uncommitted changes in your workspace.${NC}"
  echo
fi

# Get commit message
read -p "Enter a commit message for this deployment (default: 'Update documentation'): " COMMIT_MESSAGE
COMMIT_MESSAGE=${COMMIT_MESSAGE:-"Update documentation"}

# Display deployment options
echo
echo -e "${CYAN}Select a deployment method:${NC}"
echo -e "  ${GREEN}1)${NC} Direct Deployment ${YELLOW}(Recommended)${NC}"
echo "     - Builds and deploys without switching branches"
echo "     - Safe with uncommitted changes"
echo
echo -e "  ${GREEN}2)${NC} Traditional Deployment"
echo "     - Switches branches locally"
echo "     - Handles uncommitted changes by stashing"
echo
echo -e "  ${GREEN}3)${NC} Deploy Existing Site"
echo "     - Uses an already built site/ directory"
echo "     - Doesn't rebuild documentation"
echo
echo -e "  ${GREEN}4)${NC} Help & Information"
echo "     - Learn more about deployment options"
echo
echo -e "  ${GREEN}q)${NC} Quit"
echo

# Get user choice
read -p "Select an option [1-4 or q]: " CHOICE
echo

case "$CHOICE" in
  1)
    echo -e "${CYAN}Running direct deployment...${NC}"
    echo -e "This method will build documentation and deploy without switching branches."
    ./docs_create/push_site_to_ghpages.sh "$COMMIT_MESSAGE"
    ;;
  2)
    echo -e "${CYAN}Running traditional deployment...${NC}"
    echo -e "This method will stash any uncommitted changes, switch branches, and deploy."
    ./docs_create/deploy_docs.sh "$COMMIT_MESSAGE"
    ;;
  3)
    if [ ! -d "site" ]; then
      echo -e "${RED}Error: site/ directory not found.${NC}"
      echo "Would you like to build the site first? [y/n]"
      read -p "> " BUILD_SITE
      if [[ "$BUILD_SITE" =~ ^[Yy] ]]; then
        echo -e "${CYAN}Building site...${NC}"
        mkdocs build
        echo -e "${CYAN}Deploying existing site...${NC}"
        ./docs_create/push_existing_site.sh "$COMMIT_MESSAGE"
      else
        echo -e "${YELLOW}Deployment cancelled.${NC}"
      fi
    else
      echo -e "${CYAN}Deploying existing site...${NC}"
      ./docs_create/push_existing_site.sh "$COMMIT_MESSAGE"
    fi
    ;;
  4)
    echo -e "${CYAN}Deployment Options Information:${NC}"
    echo
    echo -e "${GREEN}Option 1: Direct Deployment${NC}"
    echo "This method uses a temporary directory to clone the gh-pages branch,"
    echo "builds the documentation, and updates the branch without switching your"
    echo "local working directory. This prevents issues with uncommitted changes."
    echo
    echo -e "${GREEN}Option 2: Traditional Deployment${NC}"
    echo "This method switches to the gh-pages branch locally, updates the content,"
    echo "and switches back to your original branch. It handles uncommitted changes"
    echo "by stashing them before switching and restoring them after."
    echo
    echo -e "${GREEN}Option 3: Deploy Existing Site${NC}"
    echo "This method deploys an already built site directory without rebuilding"
    echo "the documentation. It's useful when you've made manual changes to the"
    echo "built site or want to ensure exactly what gets deployed."
    echo
    echo -e "${GREEN}Setting Up GitHub Pages:${NC}"
    echo "1. Go to your repository on GitHub"
    echo "2. Navigate to Settings > Pages"
    echo "3. Under 'Source', select 'Deploy from a branch'"
    echo "4. Select the 'gh-pages' branch and '/ (root)' folder"
    echo
    echo -e "${YELLOW}For more information, see the GitHub Pages deployment guide:${NC}"
    echo "docs_create/github_pages_deployment.md"
    echo
    echo -e "${CYAN}Would you like to run a deployment now? [y/n]${NC}"
    read -p "> " RUN_DEPLOY
    if [[ "$RUN_DEPLOY" =~ ^[Yy] ]]; then
      echo -e "${CYAN}Select deployment method [1-3]:${NC}"
      read -p "> " DEPLOY_CHOICE
      case "$DEPLOY_CHOICE" in
        1)
          ./docs_create/push_site_to_ghpages.sh "$COMMIT_MESSAGE"
          ;;
        2)
          ./docs_create/deploy_docs.sh "$COMMIT_MESSAGE"
          ;;
        3)
          if [ ! -d "site" ]; then
            echo -e "${RED}Error: site/ directory not found. Build first with 'mkdocs build'${NC}"
            exit 1
          fi
          ./docs_create/push_existing_site.sh "$COMMIT_MESSAGE"
          ;;
        *)
          echo -e "${YELLOW}Invalid option. Deployment cancelled.${NC}"
          ;;
      esac
    fi
    ;;
  q|Q)
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
    ;;
  *)
    echo -e "${RED}Invalid option.${NC}"
    exit 1
    ;;
esac

echo
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Deployment completed successfully!${NC}"
  echo "Your documentation should be available at: https://[username].github.io/[repository]/"
else
  echo -e "${RED}Deployment failed.${NC}"
  echo "Check the error messages above for more information."
fi

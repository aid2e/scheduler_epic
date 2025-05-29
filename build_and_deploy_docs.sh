#!/bin/bash
# Script to build and deploy documentation to GitHub Pages
# Usage: ./build_and_deploy_docs.sh [commit_message] [deploy_message]

set -e

COMMIT_MESSAGE=${1:-"Update documentation content"}
DEPLOY_MESSAGE=${2:-"Deploy documentation update"}

echo "Building and deploying documentation..."

# Step 1: Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
  echo "You have uncommitted changes. Do you want to:"
  echo "1) Commit them with message: '$COMMIT_MESSAGE'"
  echo "2) Stash them temporarily"
  echo "3) Abort"
  read -p "Enter your choice (1-3): " choice
  
  case $choice in
    1)
      echo "Committing changes..."
      git add .
      git commit -m "$COMMIT_MESSAGE"
      ;;
    2)
      echo "Stashing changes..."
      git stash save "Temporarily stashed before documentation deployment"
      STASHED=true
      ;;
    3)
      echo "Aborting operation."
      exit 0
      ;;
    *)
      echo "Invalid choice. Aborting."
      exit 1
      ;;
  esac
fi

# Step 2: Build the documentation
echo "Building documentation..."
mkdocs build

# Step 3: Create a temporary directory for the site
echo "Creating temporary directory..."
TEMP_DIR=$(mktemp -d)
cp -r site/* $TEMP_DIR/

# Step 4: Switch to gh-pages branch or create it
if git rev-parse --verify gh-pages >/dev/null 2>&1; then
  echo "Switching to existing gh-pages branch..."
  git checkout gh-pages
else
  echo "Creating new gh-pages branch..."
  git checkout --orphan gh-pages
  git rm -rf . || true
fi

# Step 5: Remove existing content
echo "Removing existing content..."
find . -maxdepth 1 -not -path "./.git" -not -path "." -exec rm -rf {} \; || true

# Step 6: Copy the built site from the temporary directory
echo "Copying built site from temporary location..."
cp -r $TEMP_DIR/* .

# Step 7: Create .nojekyll file
echo "Creating .nojekyll file..."
touch .nojekyll

# Step 8: Add, commit, and push
echo "Committing changes to gh-pages..."
git add .
git commit -m "$DEPLOY_MESSAGE" || echo "No changes to commit"

echo "Pushing to GitHub..."
git push origin gh-pages

# Step 9: Switch back to original branch
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD@{1})
echo "Switching back to $ORIGINAL_BRANCH..."
git checkout "$ORIGINAL_BRANCH"

# Step 10: Restore stashed changes if any
if [[ "$STASHED" == "true" ]]; then
  echo "Restoring stashed changes..."
  git stash pop || echo "Note: There might be conflicts when restoring your changes"
fi

# Step 11: Clean up
echo "Cleaning up..."
rm -rf $TEMP_DIR

echo "Documentation successfully built and deployed!"
echo "It should be available at: https://[username].github.io/[repository]/"

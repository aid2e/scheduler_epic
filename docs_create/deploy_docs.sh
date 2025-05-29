#!/bin/bash
# Script to help deploy MkDocs documentation to GitHub Pages
# Usage: ./deploy_docs.sh [commit_message]

set -e

COMMIT_MESSAGE=${1:-"Update documentation"}

echo "Deploying documentation to GitHub Pages..."

# Step 1: Build the documentation
echo "Building documentation..."
mkdocs build

# Step 2: Create a temporary directory for the gh-pages branch
echo "Creating temporary directory..."
TEMP_DIR=$(mktemp -d)
cp -r site/* $TEMP_DIR/

# Step 3: Stash any uncommitted changes to avoid conflicts
echo "Stashing uncommitted changes..."
git stash push -m "Stashing changes before deploying docs" --include-untracked || true

# Step 4: Check if gh-pages branch exists
if git rev-parse --verify gh-pages >/dev/null 2>&1; then
  echo "Switching to existing gh-pages branch..."
  git checkout gh-pages
else
  echo "Creating new gh-pages branch..."
  git checkout --orphan gh-pages
  # Remove all files when creating a new branch
  git rm -rf . || true
fi

# Step 5: Remove existing content (except .git directory)
echo "Removing existing content..."
find . -maxdepth 1 -not -path "./.git" -not -path "." -exec rm -rf {} \; || true

# Step 6: Copy the built site
echo "Copying built site..."
cp -r $TEMP_DIR/* .

# Step 7: Create .nojekyll file to prevent Jekyll processing
echo "Creating .nojekyll file..."
touch .nojekyll

# Step 8: Add, commit, and push the changes
echo "Committing changes..."
git add .
git commit -m "$COMMIT_MESSAGE" || echo "No changes to commit"

echo "Pushing to GitHub..."
git push origin gh-pages

# Step 9: Switch back to the original branch
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD@{1})
echo "Switching back to original branch ($ORIGINAL_BRANCH)..."
git checkout "$ORIGINAL_BRANCH"

# Step 10: Restore uncommitted changes if there were any
if git stash list | grep -q "Stashing changes before deploying docs"; then
  echo "Restoring stashed changes..."
  git stash pop || echo "Note: There might be conflicts when restoring your changes"
fi

# Step 11: Clean up
echo "Cleaning up..."
rm -rf $TEMP_DIR

echo "Documentation successfully deployed to GitHub Pages!"
echo "It should be available at: https://[username].github.io/[repository]/"

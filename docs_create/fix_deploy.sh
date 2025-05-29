#!/bin/bash
# Emergency script to fix deployment issues when you have uncommitted changes
# Usage: ./fix_deploy.sh [commit_message]

set -e

COMMIT_MESSAGE=${1:-"Fix documentation and deploy"}

echo "Fixing deployment issues..."

# Save current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Build the documentation first while we're still on the main branch
echo "Building documentation..."
mkdocs build

# Create a temporary directory to store the site
echo "Copying site to temporary location..."
TEMP_DIR=$(mktemp -d)
cp -r site/* $TEMP_DIR/
echo "Site backed up to $TEMP_DIR"

# Stash changes with a specific message
echo "Stashing your uncommitted changes..."
git stash save "Uncommitted changes before emergency deploy fix"

# Switch to gh-pages branch or create it
if git rev-parse --verify gh-pages >/dev/null 2>&1; then
  echo "Switching to existing gh-pages branch..."
  git checkout gh-pages
else
  echo "Creating new gh-pages branch..."
  git checkout --orphan gh-pages
  git rm -rf . || true
fi

# Remove existing content
echo "Removing existing content..."
find . -maxdepth 1 -not -path "./.git" -not -path "." -exec rm -rf {} \; || true

# Copy the built site from the temporary directory
echo "Copying built site from temporary location..."
cp -r $TEMP_DIR/* .
echo "Site files restored from backup"

# Create .nojekyll file
echo "Creating .nojekyll file..."
touch .nojekyll

# Add, commit, and push
echo "Committing changes to gh-pages..."
git add .
git commit -m "$COMMIT_MESSAGE" || echo "No changes to commit"

echo "Pushing to GitHub..."
git push origin gh-pages --force

# Switch back to original branch
echo "Switching back to $CURRENT_BRANCH..."
git checkout "$CURRENT_BRANCH"

# Apply stashed changes
echo "Restoring your uncommitted changes..."
git stash pop || echo "Note: There might be conflicts to resolve"

echo "Emergency fix completed!"
echo "Documentation should be available at: https://[username].github.io/[repository]/"
echo ""
echo "Next steps:"
echo "1. Resolve any conflicts if needed"
echo "2. Commit your changes: git add . && git commit -m 'Your message'"
echo "3. For future deployments, use './deploy_docs.sh' after committing your changes"

#!/bin/bash
# Script to push an existing site directory to GitHub Pages without switching branches
# Use this when you already have a site/ directory and want to deploy it
# Usage: ./push_existing_site.sh [commit_message]

set -e

COMMIT_MESSAGE=${1:-"Update documentation"}

echo "Deploying existing site to GitHub Pages..."

# Step 1: Check if the site directory exists
if [ ! -d "site" ]; then
  echo "Error: site/ directory not found. Run 'mkdocs build' first."
  exit 1
fi

# Step 2: Check if gh-pages branch exists
if git ls-remote --heads origin gh-pages | grep -q 'gh-pages'; then
  echo "The gh-pages branch already exists on the remote."
else
  echo "Creating gh-pages branch on the remote..."
  # Create an orphan branch with no history
  git checkout --orphan gh-pages-temp
  git rm -rf .
  # Create an empty commit
  git commit --allow-empty -m "Initial gh-pages commit"
  # Push to create the branch on the remote
  git push origin gh-pages-temp:gh-pages
  # Switch back to the original branch
  git checkout -
  # Remove the temporary branch
  git branch -D gh-pages-temp
  echo "gh-pages branch created on the remote."
fi

# Step 3: Clone the gh-pages branch to a temporary directory
echo "Cloning gh-pages branch to a temporary directory..."
TEMP_DIR=$(mktemp -d)
git clone --branch gh-pages $(git config --get remote.origin.url) $TEMP_DIR

# Step 4: Copy the existing site to the cloned directory
echo "Copying existing site to the cloned directory..."
# Remove all files except .git
find $TEMP_DIR -mindepth 1 -maxdepth 1 -not -path "$TEMP_DIR/.git" -exec rm -rf {} \;
# Copy site contents
cp -r site/* $TEMP_DIR/
# Add .nojekyll file to prevent Jekyll processing
touch $TEMP_DIR/.nojekyll

# Step 5: Commit and push changes in the temporary directory
echo "Committing and pushing changes..."
cd $TEMP_DIR
git add -A
git commit -m "$COMMIT_MESSAGE" || echo "No changes to commit"
git push origin gh-pages

# Step 6: Clean up
echo "Cleaning up..."
cd -
rm -rf $TEMP_DIR

echo "Existing site successfully deployed to GitHub Pages!"
echo "It should be available at: https://[username].github.io/[repository]/"

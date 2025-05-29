#!/bin/bash
# Simple script to deploy MkDocs documentation to GitHub Pages without switching branches
# Usage: ./push_site_to_ghpages.sh [commit_message]

set -e

COMMIT_MESSAGE=${1:-"Update documentation"}

echo "Deploying documentation to GitHub Pages..."

# Step 1: Build the documentation
echo "Building documentation..."
mkdocs build

# Step 2: Check if the site directory exists
if [ ! -d "site" ]; then
  echo "Error: site/ directory not found. Build failed."
  exit 1
fi

# Step 3: Check if gh-pages branch exists
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

# Step 4: Clone the gh-pages branch to a temporary directory
echo "Cloning gh-pages branch to a temporary directory..."
TEMP_DIR=$(mktemp -d)
git clone --branch gh-pages $(git config --get remote.origin.url) $TEMP_DIR

# Step 5: Copy the built site to the cloned directory
echo "Copying built site to the cloned directory..."
# Remove all files except .git
find $TEMP_DIR -mindepth 1 -maxdepth 1 -not -path "$TEMP_DIR/.git" -exec rm -rf {} \;
# Copy site contents
cp -r site/* $TEMP_DIR/
# Add .nojekyll file to prevent Jekyll processing
touch $TEMP_DIR/.nojekyll

# Step 6: Commit and push changes in the temporary directory
echo "Committing and pushing changes..."
cd $TEMP_DIR
git add -A
git commit -m "$COMMIT_MESSAGE" || echo "No changes to commit"
git push origin gh-pages

# Step 7: Clean up
echo "Cleaning up..."
cd -
rm -rf $TEMP_DIR

echo "Documentation successfully deployed to GitHub Pages!"
echo "It should be available at: https://[username].github.io/[repository]/"

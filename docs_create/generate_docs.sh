#!/bin/bash
# Script to generate a documentation structure for MkDocs
# Usage: ./generate_docs.sh [project_name] [project_repo]

set -e

# Default values
PROJECT_NAME=${1:-"My Project"}
PROJECT_REPO=${2:-"username/repository"}
PROJECT_DESC="Documentation for ${PROJECT_NAME}"
PROJECT_AUTHOR="Author"

# Extract username and repository from the repository string
USERNAME=$(echo $PROJECT_REPO | cut -d'/' -f1)
REPOSITORY=$(echo $PROJECT_REPO | cut -d'/' -f2)

echo "Generating documentation structure for: ${PROJECT_NAME}"
echo "Repository: ${PROJECT_REPO}"

# Create the base directory structure
echo "Creating directory structure..."
mkdir -p docs/assets docs/stylesheets docs/api docs/tutorials

# Create the requirements-docs.txt file
echo "Creating requirements-docs.txt..."
cat > docs/requirements-docs.txt << EOF
mkdocs>=1.4.0
mkdocs-material>=8.5.0
pymdown-extensions>=9.0
cairosvg>=2.5.0
pillow>=9.0.0
pygments>=2.14.0
EOF

# Create the base index.md file
echo "Creating index.md..."
cat > docs/index.md << EOF
# ${PROJECT_NAME}

Welcome to the ${PROJECT_NAME} documentation.

## Overview

${PROJECT_DESC}

## Getting Started

- [Installation](installation.md)
- [Quick Start](quickstart.md)

## Tutorials

Explore our tutorials to learn how to use ${PROJECT_NAME}:

- [Tutorial 1](tutorials/tutorial1.md)
- [Tutorial 2](tutorials/tutorial2.md)

## API Reference

Detailed API documentation:

- [API Overview](api/index.md)
EOF

# Create basic documentation files
echo "Creating basic documentation files..."
cat > docs/installation.md << EOF
# Installation

## Prerequisites

- Python 3.7+
- Pip

## Install from PyPI

\`\`\`bash
pip install your-package-name
\`\`\`

## Install from Source

\`\`\`bash
git clone https://github.com/${PROJECT_REPO}.git
cd $(basename ${REPOSITORY})
pip install .
\`\`\`
EOF

cat > docs/quickstart.md << EOF
# Quick Start

This guide will help you get started with ${PROJECT_NAME}.

## Basic Usage

\`\`\`python
# Import the library
import your_package

# Initialize
client = your_package.Client()

# Do something
result = client.process()
print(result)
\`\`\`

## Next Steps

Check out the [tutorials](tutorials/index.md) for more examples.
EOF

# Create API reference section
echo "Creating API reference files..."
cat > docs/api/index.md << EOF
# API Reference

This section contains detailed API documentation for ${PROJECT_NAME}.

## Classes

- [Class1](class1.md)
- [Class2](class2.md)

## Functions

- [function1](function1.md)
- [function2](function2.md)
EOF

# Create tutorials section
echo "Creating tutorials files..."
cat > docs/tutorials/index.md << EOF
# Tutorials

Learn how to use ${PROJECT_NAME} with these step-by-step tutorials.

## Basic Tutorials

- [Tutorial 1](tutorial1.md)
- [Tutorial 2](tutorial2.md)

## Advanced Tutorials

- [Advanced Tutorial 1](advanced_tutorial1.md)
EOF

cat > docs/tutorials/tutorial1.md << EOF
# Tutorial 1: Getting Started

This tutorial guides you through the basics of using ${PROJECT_NAME}.

## Prerequisites

- ${PROJECT_NAME} installed
- Basic Python knowledge

## Step 1: Setup

\`\`\`python
import your_package

# Initialize
client = your_package.Client()
\`\`\`

## Step 2: Configuration

Configure your client:

\`\`\`python
client.configure(option1="value1", option2="value2")
\`\`\`

## Step 3: Run

Execute your first operation:

\`\`\`python
result = client.process()
print(result)
\`\`\`

## Conclusion

You've completed your first operation with ${PROJECT_NAME}!
EOF

# Create GitBook-like CSS
echo "Creating GitBook-like CSS..."
cat > docs/stylesheets/gitbook.css << EOF
/* GitBook-like styles */
:root {
  --md-primary-fg-color: #4051b5;
  --md-primary-fg-color--light: #7880c3;
  --md-primary-fg-color--dark: #303fa1;
}

/* Make navigation sidebar more like GitBook */
.md-sidebar--primary {
  background-color: #fafafa;
}

[data-md-color-scheme="slate"] .md-sidebar--primary {
  background-color: #1e1e1e;
}

/* Improve readability of main content */
.md-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem 2rem;
}

/* Enhance code blocks */
.highlight pre {
  border-radius: 4px;
}

/* Make headings more prominent */
.md-content h1 {
  font-weight: 600;
  margin-bottom: 2rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

[data-md-color-scheme="slate"] .md-content h1 {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* Nice link styling */
.md-content a:not(.md-button) {
  color: var(--md-primary-fg-color);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s ease;
}

.md-content a:not(.md-button):hover {
  border-bottom-color: var(--md-primary-fg-color);
}
EOF

# Create a placeholder for logo and favicon
echo "Creating placeholder images..."
echo "Add your logo here" > docs/assets/README.md

# Create mkdocs.yml
echo "Creating mkdocs.yml..."
cat > mkdocs.yml << EOF
site_name: ${PROJECT_NAME}
site_description: ${PROJECT_DESC}
site_author: ${PROJECT_AUTHOR}
site_url: https://${USERNAME}.github.io/${REPOSITORY}/
repo_url: https://github.com/${PROJECT_REPO}
repo_name: ${PROJECT_REPO}

# Theme configuration
theme:
  name: material
  logo: assets/logo.png
  favicon: assets/favicon.png
  palette:
    # Light mode
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/weather-night
        name: Switch to dark mode
    # Dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/weather-sunny
        name: Switch to light mode
  features:
    - navigation.top
    - toc.follow
    - content.code.copy
    - content.code.annotate
    - content.action.edit
    - search.highlight
    - search.suggest
    - navigation.tabs
  icon:
    repo: fontawesome/brands/github

# Extra configuration
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/${PROJECT_REPO}
      name: ${PROJECT_NAME} on GitHub
  
  # Add GitHub edit capabilities
  repo_icon: github
  edit_uri: edit/main/docs/

# Add custom CSS to make it more GitBook-like
extra_css:
  - stylesheets/gitbook.css

# Markdown extensions for richer content
markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - toc:
      permalink: true
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.tabbed:
      alternate_style: true 
  - pymdownx.tasklist:
      custom_checkbox: true

# Navigation structure
nav:
  - Home: index.md
  - Installation: installation.md
  - Quick Start: quickstart.md
  - Tutorials:
    - Overview: tutorials/index.md
    - Tutorial 1: tutorials/tutorial1.md
  - API Reference:
    - Overview: api/index.md
  
# Plugins for additional functionality
plugins:
  - search
EOF

# Create a GitHub Actions workflow file
echo "Creating GitHub Actions workflow..."
mkdir -p .github/workflows
cat > .github/workflows/deploy-docs.yml << EOF
name: Deploy Documentation

on:
  push:
    branches:
      - main

# Sets permissions of the GITHUB_TOKEN to allow deployment to GitHub Pages
permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          # Install Cairo for SVG support
          sudo apt-get update
          sudo apt-get install -y libcairo2-dev pkg-config python3-dev
          # Install documentation requirements
          pip install -r docs/requirements-docs.txt
      
      - name: Configure Git
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
      
      - name: Deploy documentation
        run: |
          # Try up to 3 times to deploy, handling potential race conditions
          max_attempts=3
          attempt=1
          
          while [ \$attempt -le \$max_attempts ]; do
            echo "Deployment attempt \$attempt of \$max_attempts"
            
            if mkdocs gh-deploy --force --clean; then
              echo "Deployment successful!"
              break
            else
              if [ \$attempt -eq \$max_attempts ]; then
                echo "Failed all \$max_attempts deployment attempts"
                exit 1
              fi
              
              echo "Deployment attempt failed. Fetching latest changes and retrying..."
              git fetch origin gh-pages || true
              sleep 5
            fi
            
            attempt=\$((attempt+1))
          done
EOF

echo "Creating README.md with instructions..."
cat > README.md << EOF
# ${PROJECT_NAME} Documentation

This repository contains the documentation for ${PROJECT_NAME}.

## Getting Started

1. Install MkDocs and required packages:

\`\`\`bash
pip install -r docs/requirements-docs.txt
\`\`\`

2. Serve the documentation locally:

\`\`\`bash
mkdocs serve
\`\`\`

3. View the documentation at http://127.0.0.1:8000/

## Building for Production

\`\`\`bash
mkdocs build
\`\`\`

This will generate the static HTML files in the \`site/\` directory.

## Deploying to GitHub Pages

There are two ways to deploy your documentation to GitHub Pages:

### Option 1: Automated Deployment with GitHub Actions

The included GitHub Actions workflow automatically builds and deploys your documentation when you push to the main branch.

To enable it:
1. Go to your repository settings > Pages
2. Set the source to "GitHub Actions"

### Option 2: Manual Deployment

If you prefer to manually deploy your documentation:

1. Build the documentation:
   \`\`\`bash
   mkdocs build
   \`\`\`

2. Deploy the static site to the gh-pages branch:
   \`\`\`bash
   # Switch to gh-pages branch (create if it doesn't exist)
   git checkout gh-pages || git checkout --orphan gh-pages
   
   # Remove existing content
   find . -maxdepth 1 -not -path "./.git" -not -path "." -exec rm -rf {} \;
   
   # Copy the built site
   cp -r site/* .
   
   # Add a .nojekyll file to disable Jekyll processing
   touch .nojekyll
   
   # Commit and push
   git add .
   git commit -m "Update documentation"
   git push origin gh-pages
   
   # Switch back to original branch
   git checkout -
   \`\`\`

## Documentation Structure

- \`docs/\`: Documentation source files
- \`site/\`: Built documentation (generated)
- \`mkdocs.yml\`: MkDocs configuration

## Contributing

1. Fork this repository
2. Make your changes
3. Submit a pull request
EOF

echo "Documentation structure generated successfully!"
echo "To preview the documentation, run: cd $(pwd) && mkdocs serve"
echo "Don't forget to add your logo.png and favicon.png to the docs/assets directory."

# Create the deployment scripts
echo "Creating deployment scripts..."

# Standard deployment script (with stashing)
cat > deploy_docs.sh << EOF
#!/bin/bash
# Script to help deploy MkDocs documentation to GitHub Pages
# Usage: ./deploy_docs.sh [commit_message]

set -e

COMMIT_MESSAGE=\${1:-"Update documentation"}

echo "Deploying documentation to GitHub Pages..."

# Step 1: Build the documentation
echo "Building documentation..."
mkdocs build

# Step 2: Create a temporary directory for the gh-pages branch
echo "Creating temporary directory..."
TEMP_DIR=\$(mktemp -d)
cp -r site/* \$TEMP_DIR/

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
cp -r \$TEMP_DIR/* .

# Step 7: Create .nojekyll file to prevent Jekyll processing
echo "Creating .nojekyll file..."
touch .nojekyll

# Step 8: Add, commit, and push the changes
echo "Committing changes..."
git add .
git commit -m "\$COMMIT_MESSAGE" || echo "No changes to commit"

echo "Pushing to GitHub..."
git push origin gh-pages

# Step 9: Switch back to the original branch
ORIGINAL_BRANCH=\$(git rev-parse --abbrev-ref HEAD@{1})
echo "Switching back to original branch (\$ORIGINAL_BRANCH)..."
git checkout "\$ORIGINAL_BRANCH"

# Step 10: Restore uncommitted changes if there were any
if git stash list | grep -q "Stashing changes before deploying docs"; then
  echo "Restoring stashed changes..."
  git stash pop || echo "Note: There might be conflicts when restoring your changes"
fi

# Step 11: Clean up
echo "Cleaning up..."
rm -rf \$TEMP_DIR

echo "Documentation successfully deployed to GitHub Pages!"
echo "It should be available at: https://[username].github.io/[repository]/"
EOF

# Simple deployment script (requires committed changes)
cat > deploy_docs_simple.sh << EOF
#!/bin/bash
# Simple script to deploy MkDocs documentation to GitHub Pages
# This script assumes you've committed all your changes first
# Usage: ./deploy_docs_simple.sh [commit_message]

set -e

COMMIT_MESSAGE=\${1:-"Update documentation"}

echo "Deploying documentation to GitHub Pages..."

# Check if there are uncommitted changes
if [[ -n \$(git status -s) ]]; then
  echo "Error: You have uncommitted changes. Please commit or stash them first."
  echo "Run 'git status' to see the changes."
  exit 1
fi

# Build the documentation
echo "Building documentation..."
mkdocs build

# Switch to gh-pages branch or create it
if git rev-parse --verify gh-pages >/dev/null 2>&1; then
  git checkout gh-pages
else
  git checkout --orphan gh-pages
  git rm -rf . || true
fi

# Remove existing content
find . -maxdepth 1 -not -path "./.git" -not -path "." -exec rm -rf {} \; || true

# Copy the built site
cp -r site/* .

# Create .nojekyll file
touch .nojekyll

# Add, commit, and push
git add .
git commit -m "\$COMMIT_MESSAGE" || echo "No changes to commit"
git push origin gh-pages

# Switch back
git checkout -

echo "Documentation successfully deployed to GitHub Pages!"
echo "It should be available at: https://[username].github.io/[repository]/"
EOF

# Make the deployment scripts executable
chmod +x deploy_docs.sh deploy_docs_simple.sh

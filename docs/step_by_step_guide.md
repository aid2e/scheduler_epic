# Step-by-Step Documentation Guide

This guide provides detailed instructions for creating, building, and deploying documentation for your project using MkDocs and GitHub Pages.

## Prerequisites

- Git installed
- Python 3.7+ installed
- A GitHub repository for your project

## Step 1: Set Up Documentation Structure

### Option A: Using the Automatic Generator

If you're starting from scratch, use the provided documentation generator script:

```bash
cd /mnt/d/AID2E/scheduler_epic
# Make the script executable if needed
chmod +x docs_create/generate_docs.sh
# Run the generator (replace with your project details)
./docs_create/generate_docs.sh "Your Project Name" "username/repository"
```

### Option B: Manual Setup

If you prefer to set up manually:

1. Create a docs directory and basic structure:

```bash
mkdir -p docs/assets docs/stylesheets docs/api docs/tutorials
```

2. Create a requirements file for documentation:

```bash
cat > docs/requirements-docs.txt << EOF
mkdocs>=1.4.0
mkdocs-material>=8.5.0
pymdown-extensions>=9.0
cairosvg>=2.5.0
pillow>=9.0.0
pygments>=2.14.0
EOF
```

3. Create a basic mkdocs.yml configuration in your project root:

You can also use `generate_docs.sh` to generate the mkdocs.yml file which is located in `docs_create` folder.
```bash
cat > mkdocs.yml << EOF
site_name: Project NAME
site_description: Project description
site_author: AID2E Team
site_url: SITE URL
repo_url: https://github.com/aid2e/scheduler_epic
repo_name: aid2e/scheduler_epic

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
    # Your existing features
    - navigation.top
    - toc.follow
    - content.code.copy
    - content.code.annotate
    - content.action.edit
    - search.highlight
    - search.suggest
    - navigation.tabs
    # Add these features to enable the left sidebar
    - navigation.sections
    - navigation.indexes
    - navigation.expand
    # Keep these existing features
    - navigation.tabs.sticky
    - navigation.tabs.sticky_header
    - navigation.tabs.instant
    - navigation.tabs.autohide
    - navigation.instant
    - header.autohide
  icon:
    repo: fontawesome/brands/github

# Extra configuration
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/aid2e/scheduler_epic
      name: AID2E Scheduler on GitHub
  
  # Add GitHub edit capabilities
  repo_icon: github
  edit_uri: edit/main/docs/

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
EOF
```

## Step 2: Install Documentation Requirements

Install the required packages for building the documentation:

```bash
pip install -r docs/requirements-docs.txt
```

## Step 3: Create Basic Documentation Content

At minimum, you need an index.md file in your docs directory:

```bash
cat > docs/index.md << EOF
# Project Documentation

Welcome to the project documentation.

## Overview

Describe your project here.

## Getting Started

- [Installation](installation.md)
- [Quick Start](quickstart.md)
EOF
```

## Step 4: Add Documentation for Your Project

1. Create documentation files for your project components
2. Organize them in appropriate directories (tutorials, API reference, etc.)
3. Update the navigation structure in mkdocs.yml

Example for adding a tutorial:

```bash
cat > docs/tutorials/index.md << EOF
# Tutorials

This section contains tutorials for using the project.

## Available Tutorials

- [Tutorial 1](tutorial1.md)
EOF
```

### Automatically Generate API Documentation

To automatically generate API documentation from your source code:

1. Use the provided API documentation generator script:

```bash
# Make the script executable
chmod +x docs_create/generate_api_docs.py

# Generate API documentation
./docs_create/generate_api_docs.py
```

This script:
- Parses your Python modules and classes
- Extracts docstrings and signatures
- Generates formatted Markdown files in the `docs/api/` directory
- Creates a consistent API reference with proper formatting

2. For convenience, you can use the update script that also previews and deploys:

```bash
./update_api_docs.sh "Update API documentation"
```

This automatically:
- Generates the API documentation
- Starts a preview server so you can review the changes
- Optionally deploys to GitHub Pages when you're satisfied

## Step 5: Preview Your Documentation Locally

Preview your documentation to check how it looks:

```bash
cd /mnt/d/AID2E/scheduler_epic
mkdocs serve
```

This will start a local server at http://127.0.0.1:8000/ where you can preview your documentation.

## Step 6: Build Your Documentation

Once you're satisfied with your documentation, build it:

```bash
cd /mnt/d/AID2E/scheduler_epic
mkdocs build
```

This will create a `site` directory containing the static HTML files.

## Step 7: Deploy to GitHub Pages

There are multiple options for deploying your documentation to GitHub Pages:

### Option A: Using GitHub Actions (Automated Deployment)

1. Create a GitHub Actions workflow file:

```bash
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
      
      - name: Generate API Documentation
        run: |
          # Generate API documentation from source code
          python docs_create/generate_api_docs.py
      
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
```

2. Push your changes to GitHub:

```bash
git add .
git commit -m "Add documentation and GitHub Actions workflow"
git push origin main
```

3. Configure GitHub Pages in your repository settings to use the gh-pages branch.

### Option B: Direct Deployment without Branch Switching

This approach avoids switching branches locally, which prevents issues with uncommitted changes. Instead, it clones the gh-pages branch to a temporary directory, updates it with your built site, and pushes it back:

```bash
cd /mnt/d/AID2E/scheduler_epic
./docs_create/push_site_to_ghpages.sh "Update documentation"
```

This script:
1. Builds the documentation
2. Creates the gh-pages branch remotely if it doesn't exist
3. Clones the gh-pages branch to a temporary directory
4. Copies your built site to this temporary directory
5. Commits and pushes the changes
6. Cleans up the temporary directory

If you've already built the site and don't want to rebuild:

```bash
cd /mnt/d/AID2E/scheduler_epic
./docs_create/push_existing_site.sh "Deploy existing site"
```

### Option C: Traditional Deployment with Branch Switching

### Option C: Traditional Deployment with Branch Switching

You can manually deploy your documentation by switching branches:

#### Using the Standard Deployment Script

This script handles uncommitted changes by stashing them:

```bash
cd /mnt/d/AID2E/scheduler_epic
./docs_create/deploy_docs.sh "Update documentation"
```

#### Using the Simple Deployment Script

This script requires you to commit your changes first:

```bash
cd /mnt/d/AID2E/scheduler_epic
# Commit your changes first
git add .
git commit -m "Update documentation content"
# Then deploy
./docs_create/deploy_docs_simple.sh "Deploy documentation"
```

#### Emergency Fix Script

For handling deployment issues:

```bash
cd /mnt/d/AID2E/scheduler_epic
./docs_create/fix_deploy.sh "Fix and deploy documentation"
```

## Step 8: Verify Your Documentation

After deployment, your documentation should be available at:

```
https://aid2e.github.io/[repository]/
```

Visit this URL to ensure your documentation is correctly deployed.

## Step 9: Add a Link to Your Documentation in README

Update your README.md to include a link to your documentation:

```markdown
## Documentation

Comprehensive documentation is available at: https://aid2e.github.io/[repository]/
```

## Maintenance and Updates

To update your documentation:

1. Make changes to your Markdown files in the `docs/` directory
2. Preview changes locally with `mkdocs serve`
3. Build with `mkdocs build`
4. Deploy using your preferred method from Step 8

## Troubleshooting

### Uncommitted Changes Error

If you see an error about uncommitted changes when deploying:

```
error: Your local changes to the following files would be overwritten by checkout:
        [list of files]
Please commit your changes or stash them before you switch branches.
Aborting
```

Use one of these solutions:

1. Commit your changes before deploying:
   ```bash
   git add .
   git commit -m "Your message here"
   ```

2. Use the `deploy_docs.sh` script which automatically handles stashing and restoring changes

3. Use the emergency fix script:
   ```bash
   ./docs_create/fix_deploy.sh "Fix and deploy"
   ```

### 404 Page Not Found

If your site shows a 404 error:

1. Make sure GitHub Pages is enabled in your repository settings
2. Verify the gh-pages branch exists and contains your documentation
3. Check the source settings in GitHub Pages configuration

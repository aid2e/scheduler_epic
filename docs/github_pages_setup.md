# Setting Up Documentation Hosting on GitHub

This guide explains how to set up hosting for your project documentation on GitHub Pages using MkDocs with the Material theme and a GitBook-like appearance.

## Prerequisites

- GitHub repository for your project
- Python 3.7+ installed
- Access to GitHub Actions

## Step 1: Install MkDocs and Required Extensions

First, create a requirements file for documentation dependencies (requirements-docs.txt):

```bash
# Create a requirements file for documentation
cat > docs/requirements-docs.txt << EOF
mkdocs>=1.4.0
mkdocs-material>=8.5.0
pymdown-extensions>=9.0
cairosvg>=2.5.0
pillow>=9.0.0
pygments>=2.14.0
EOF

# Install the requirements
pip install -r docs/requirements-docs.txt
```

## Step 2: Create Documentation Directory Structure

Create a `docs` directory in the root of your repository with the following structure:

```
docs/
├── index.md                  # Home page
├── installation.md           # Installation guide
├── quickstart.md             # Quick start guide
├── architecture.md           # Architecture overview
├── requirements-docs.txt     # Documentation dependencies
├── assets/                   # Images and other assets
│   ├── logo.png
│   └── favicon.png
├── stylesheets/              # Custom CSS
│   └── gitbook.css
├── api/                      # API documentation
│   └── index.md
└── tutorials/                # Tutorials
    └── index.md
```

Create the base structure with:

```bash
# Create the directory structure
mkdir -p docs/assets docs/stylesheets docs/api docs/tutorials
```

## Step 3: Create MkDocs Configuration

Create a file named `mkdocs.yml` in the root of your repository:

```yaml
site_name: Scheduler for AID2E
site_description: A Python library for scheduling and managing optimization trials for the ePIC EIC detector design using Ax
site_author: AID2E Team
site_url: https://aid2e.github.io/scheduler_epic/
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
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.indexes
    - navigation.top
    - toc.follow
    - content.code.copy
    - content.code.annotate
    - content.action.edit
    - search.highlight
    - search.suggest
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
```

This configuration includes:
- Material theme with light/dark mode toggle
- Custom GitBook-like styling
- GitHub repository integration
- Enhanced navigation features
- Syntax highlighting and other Markdown extensions

nav:
  - Home: index.md
  - Installation: installation.md
  - Quick Start: quickstart.md
  - Tutorials:
    - tutorials/index.md
    - Basic Detector Optimization: tutorials/detector_optimization.md
    - Slurm Execution: tutorials/slurm_execution.md
    - Container-Based Optimization: tutorials/container_based_optimization.md
    - Batch Trial Submission: tutorials/batch_trial_submission.md
  - API Reference:
    - api/index.md
    - AxScheduler: api/ax_scheduler.md
    - Trial: api/trial.md
    - Job: api/job.md
    - Runners: api/runners.md
  - Architecture: architecture.md
```

## Step 4: Preview Documentation Locally

You can preview your documentation locally by running:

```bash
mkdocs serve
```

This will start a local server at http://127.0.0.1:8000/ where you can preview your documentation.

## Step 5: Configure GitHub Actions for Deployment

Create a GitHub Actions workflow file at `.github/workflows/deploy-docs.yml`:

```yaml
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
          
          while [ $attempt -le $max_attempts ]; do
            echo "Deployment attempt $attempt of $max_attempts"
            
            if mkdocs gh-deploy --force --clean; then
              echo "Deployment successful!"
              break
            else
              if [ $attempt -eq $max_attempts ]; then
                echo "Failed all $max_attempts deployment attempts"
                exit 1
              fi
              
              echo "Deployment attempt failed. Fetching latest changes and retrying..."
              git fetch origin gh-pages || true
              sleep 5
            fi
            
            attempt=$((attempt+1))
          done
```

This workflow includes retry logic to handle potential race conditions during deployment, which can sometimes occur with GitHub Pages.

## Step 6: Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to Settings > Pages
3. Under "Source", select "GitHub Actions"
4. Commit and push your changes to the main branch

After pushing your changes, GitHub Actions will automatically build and deploy your documentation to GitHub Pages. The documentation will be available at:

```
https://<username>.github.io/<repository>/
```

## Step 7: Add a Link to Your Documentation in README

Update your README.md to include a link to your documentation:

```markdown
## Documentation

Comprehensive documentation is available at: https://aid2e.github.io/scheduler_epic/
```

## Updating Documentation

To update your documentation:

1. Make changes to your Markdown files in the `docs/` directory
2. Commit and push your changes to the main branch
3. GitHub Actions will automatically rebuild and deploy your documentation

## Additional Configuration Options

### Removing the Left Navigation Sidebar

If you want to remove the left navigation sidebar to reduce redundancy, modify the `features` section in your `mkdocs.yml`:

```yaml
theme:
  features:
    # Remove these lines to disable the left sidebar
    # - navigation.sections
    # - navigation.expand
    # - navigation.indexes
    
    # Keep these features
    - navigation.top
    - toc.follow
    - content.code.copy
    - content.code.annotate
    - content.action.edit
    - search.highlight
    - search.suggest
    - navigation.tabs
```

You can also add custom CSS to hide the sidebar completely by adding this to `docs/stylesheets/gitbook.css`:

```css
/* Hide the left sidebar completely */
.md-sidebar--primary {
  display: none !important;
}

/* Adjust the main content width when sidebar is hidden */
.md-content {
  max-width: 1000px;
  margin: 0 auto;
}
```

### Adding a Custom Domain

If you want to use a custom domain for your documentation:

1. Go to your repository's Settings > Pages
2. Under "Custom domain", enter your domain name and save
3. Create a CNAME file in the `docs/` directory with your domain name

### Adding Search Functionality

MkDocs Material theme includes search functionality by default. You can customize it in the `mkdocs.yml` file:

```yaml
plugins:
  - search:
      lang: en
```

### Adding Analytics

You can add Google Analytics to track documentation usage:

```yaml
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

Replace `G-XXXXXXXXXX` with your Google Analytics property ID.

## GitBook-Like Styling

To achieve a GitBook-like appearance for our documentation, we've added custom CSS. Create a file at `docs/stylesheets/gitbook.css`:

```css
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
```

Then reference this CSS file in your `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/gitbook.css
```

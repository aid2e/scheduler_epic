# Setting Up Documentation Hosting on GitHub

This guide explains how to set up hosting for your Scheduler documentation on GitHub Pages using MkDocs.

## Prerequisites

- GitHub repository for your Scheduler project
- Python 3.7+ installed

## Step 1: Install MkDocs and Required Extensions

First, install MkDocs and the Material theme:

```bash
pip install mkdocs mkdocs-material
```

## Step 2: Create MkDocs Configuration

Create a file named `mkdocs.yml` in the root of your repository:

```yaml
site_name: Scheduler for AID2E
site_description: A Python library for scheduling and managing optimization trials for the ePIC EIC detector design using Ax
site_author: Your Name
repo_url: https://github.com/yourusername/scheduler
repo_name: yourusername/scheduler

theme:
  name: material
  palette:
    primary: indigo
    accent: indigo
  icon:
    repo: fontawesome/brands/github
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - content.code.copy

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.inlinehilite
  - pymdownx.tabbed
  - pymdownx.critic
  - pymdownx.tasklist:
      custom_checkbox: true
  - admonition
  - toc:
      permalink: true

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

## Step 3: Preview Documentation Locally

You can preview your documentation locally by running:

```bash
mkdocs serve
```

This will start a local server at http://127.0.0.1:8000/ where you can preview your documentation.

## Step 4: Configure GitHub Actions for Deployment

Create a GitHub Actions workflow file at `.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install mkdocs mkdocs-material
      
      - name: Deploy documentation
        run: mkdocs gh-deploy --force --clean
```

## Step 5: Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to Settings > Pages
3. Under "Source", select "GitHub Actions"
4. Commit and push your changes to the main branch

After pushing your changes, GitHub Actions will automatically build and deploy your documentation to GitHub Pages. The documentation will be available at:

```
https://yourusername.github.io/scheduler/
```

## Step 6: Add a Link to Your Documentation in README

Update your README.md to include a link to your documentation:

```markdown
## Documentation

Comprehensive documentation is available at: https://yourusername.github.io/scheduler/
```

## Updating Documentation

To update your documentation:

1. Make changes to your Markdown files in the `docs/` directory
2. Commit and push your changes to the main branch
3. GitHub Actions will automatically rebuild and deploy your documentation

## Additional Configuration Options

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

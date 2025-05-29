# Scheduler for AID2E Documentation

This directory contains the documentation for the Scheduler for AID2E project, built using [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/).

## Setup

To work on the documentation locally, you'll need to install the required dependencies:

```bash
pip install -r requirements-docs.txt
```

## Local Development

To start a local development server that will watch for changes and auto-reload:

```bash
mkdocs serve
```

This will start a server at http://localhost:8000 where you can preview your changes.

## Documentation Structure

- `index.md`: Home page
- `installation.md`: Installation instructions
- `quickstart.md`: Getting started guide
- `api/`: API reference documentation
- `tutorials/`: Step-by-step guides
- `assets/`: Images, logo, and other static assets
- `stylesheets/`: Custom CSS
- `overrides/`: Custom HTML templates

## Adding New Pages

1. Create a new Markdown file in the appropriate directory
2. Add the page to the navigation in `mkdocs.yml`

## Deployment

The documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch.

### Manual Deployment

If needed, you can manually deploy the documentation with:

```bash
mkdocs gh-deploy --force --clean
```

## Styling

The documentation uses a GitBook-like style, customized through the `stylesheets/gitbook.css` file.

## Tips

- Use admonitions (note, warning, tip) for callouts
- Include code examples with syntax highlighting
- Add diagrams where appropriate to illustrate concepts

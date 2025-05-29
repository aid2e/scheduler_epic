# Enhanced GitHub Pages Deployment Options

We've improved the GitHub Pages deployment process with multiple options to accommodate different workflows and prevent common issues.

## Option 1: GitHub Actions (Automated Deployment)
- **Best for**: Teams collaborating on documentation
- **How it works**: GitHub automatically builds and deploys when changes are pushed
- **Benefits**: No manual steps required after initial setup
- **File**: `.github/workflows/deploy-docs.yml`

## Option 2: Direct Deployment (No Branch Switching)
- **Best for**: Working with uncommitted changes or avoiding branch switching
- **How it works**: Uses a temporary directory to clone gh-pages branch and update it
- **Benefits**: Prevents "uncommitted changes" errors completely
- **Files**:
  - `push_site_to_ghpages.sh` - Builds and deploys in one step
  - `push_existing_site.sh` - Deploys an existing site directory

## Option 3: Traditional Deployment (Branch Switching)
- **Best for**: Simple deployments when workflow is clean
- **How it works**: Switches branches locally, updates content, then switches back
- **Benefits**: Standard approach, well-documented
- **Files**:
  - `deploy_docs.sh` - Handles uncommitted changes by stashing
  - `deploy_docs_simple.sh` - Requires committing changes first
  - `fix_deploy.sh` - Emergency fix for deployment issues

## Quick Reference

### Using Option 2 (Recommended)

```bash
# Build and deploy in one step
./docs_create/push_site_to_ghpages.sh "Update documentation"

# Or if you've already built the site
./docs_create/push_existing_site.sh "Deploy existing site"
```

### Using Option 1 (GitHub Actions)

1. Enable GitHub Pages in repository settings (Source: GitHub Actions)
2. Push changes to trigger workflow:
```bash
git add .
git commit -m "Update documentation"
git push origin main
```

### Using Option 3 (Traditional)

```bash
# With stashing for uncommitted changes
./docs_create/deploy_docs.sh "Update documentation"

# Or the simple version (requires committed changes)
./docs_create/deploy_docs_simple.sh "Deploy documentation"
```

## Best Practices

1. **Preview locally** before deploying: `mkdocs serve`
2. **Include meaningful commit messages** describing documentation changes
3. **Use descriptive page titles** and organize content logically
4. **Keep documentation up-to-date** with code changes
5. **Consider automating** with GitHub Actions for larger projects

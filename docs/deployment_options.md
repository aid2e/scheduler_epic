# Documentation Deployment Options

This guide covers all available options for deploying your MkDocs documentation to GitHub Pages, with pros and cons for each approach.

## Interactive Deployment

We've created an interactive script that guides you through the deployment process:

```bash
./interactive_deploy_docs.sh
```

This script will:
1. Check your workspace for uncommitted changes
2. Ask for a commit message
3. Present deployment options with explanations
4. Execute your chosen deployment method

This is the recommended approach for most users, especially those new to documentation deployment.

## Direct Deployment (No Branch Switching)

The direct deployment approach avoids switching branches locally, which prevents issues with uncommitted changes.

### Option 1: Build and Deploy in One Step

```bash
./docs_create/push_site_to_ghpages.sh "Your commit message"
```

This script:
- Builds the documentation using MkDocs
- Creates the gh-pages branch remotely if it doesn't exist
- Clones the gh-pages branch to a temporary directory
- Copies your built site to this temporary directory
- Commits and pushes the changes
- Cleans up without touching your working directory

### Option 2: Deploy an Existing Site

If you've already built the site (e.g., with `mkdocs build`) and want to deploy it without rebuilding:

```bash
./docs_create/push_existing_site.sh "Your commit message"
```

This works the same as the previous script but skips the build step.

### Pros and Cons of Direct Deployment

**Pros:**
- Works with uncommitted changes in your workspace
- No branch switching required
- Prevents accidental loss of work
- Cleaner approach that isolates deployment from development

**Cons:**
- Slightly more complex implementation
- Requires creating a temporary directory

## Traditional Deployment (Branch Switching)

The traditional approach involves switching to the gh-pages branch locally, updating content, then switching back.

### Option 1: With Automatic Stashing

```bash
./docs_create/deploy_docs.sh "Your commit message"
```

This script:
- Builds the documentation
- Stashes any uncommitted changes
- Switches to the gh-pages branch (creates it if needed)
- Updates the content
- Commits and pushes the changes
- Switches back to your original branch
- Restores your stashed changes

### Option 2: Simple Deployment (Requires Clean Workspace)

```bash
./docs_create/deploy_docs_simple.sh "Your commit message"
```

This script requires a clean workspace with all changes committed.

### Pros and Cons of Traditional Deployment

**Pros:**
- Well-documented, standard approach
- More straightforward implementation
- Widely used in the community

**Cons:**
- Requires branch switching
- Can cause issues with uncommitted changes
- Requires stashing/unstashing for safety

## Automated Deployment with GitHub Actions

For teams or larger projects, automated deployment via GitHub Actions is recommended.

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
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r docs/requirements-docs.txt
      - run: mkdocs gh-deploy --force
```

### Pros and Cons of GitHub Actions

**Pros:**
- Fully automated on push
- No manual deployment required
- Consistent build environment
- No local setup needed for deployment

**Cons:**
- Requires initial GitHub Actions setup
- Less control over exact deployment process
- May have a delay between push and deployment

## Best Practices for Any Deployment Method

1. **Preview locally before deploying**:
   ```bash
   mkdocs serve
   ```

2. **Use the requirements file for consistent dependencies**:
   ```bash
   pip install -r docs/requirements-docs.txt
   ```

3. **Include meaningful commit messages** describing documentation changes

4. **Monitor your deployment** by checking your GitHub Pages URL after deployment

5. **Add a .nojekyll file** to prevent GitHub Pages from processing your site with Jekyll

## Troubleshooting

### Documentation Not Updating

If your GitHub Pages site is not updating after deployment:
1. Check that the gh-pages branch has the latest content
2. Ensure GitHub Pages is configured to use the gh-pages branch
3. Look for any error messages in GitHub Actions (if using)
4. Try forcing a rebuild by making a small change and redeploying

### Broken Links or Missing Content

If your deployed site has broken links or missing content:
1. Check that all relative links are correct
2. Ensure all referenced files are committed to the repository
3. Verify that the site structure matches your navigation configuration in `mkdocs.yml`

### Styling Issues

If your site is missing styles or appears broken:
1. Check that your theme configuration is correct
2. Ensure all CSS files are properly referenced
3. Add `use_directory_urls: false` to your `mkdocs.yml` if needed

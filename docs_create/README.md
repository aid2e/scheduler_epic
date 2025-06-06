# Deploying Documentation to GitHub Pages

This guide ### 2. Deploy using the script

   Use the provided `deploy_docs.sh` script:

   ```bash
   ./deploy_docs.sh "Your commit message"
   ```

   This script:
   - Builds the documentation
   - Stashes any uncommitted changes to avoid conflicts
   - Switches to the gh-pages branch (or creates it if it doesn't exist)
   - Replaces the content with the new build
   - Commits and pushes the changes
   - Switches back to your original branch
   - Restores your uncommitted changes

   **Note:** It's still best practice to commit your changes before deploying.s how to deploy your MkDocs documentation to GitHub Pages.

## Prerequisites

- Git installed
- MkDocs installed
- A GitHub repository with your documentation

## Deployment Options

There are three main ways to deploy your documentation to GitHub Pages:

### Option 1: Automated Deployment with GitHub Actions (Recommended for large automated projects)

This approach uses GitHub Actions to automatically build and deploy your documentation whenever you push changes to your repository.

1. **Setup GitHub Actions workflow**

   This is already included in the documentation structure generated by the `generate_docs.sh` script. The workflow file is located at `.github/workflows/deploy-docs.yml`.

2. **Enable GitHub Pages**

   - Go to your repository on GitHub
   - Navigate to Settings > Pages
   - Under "Source", select "GitHub Actions"

3. **Push your changes**

   ```bash
   git add .
   git commit -m "Add documentation"
   git push origin main
   ```

4. **Monitor deployment**

   - Go to the "Actions" tab in your GitHub repository
   - You should see a workflow running
   - Once completed, your documentation will be available at `https://<username>.github.io/<repository>/`

### Option 2: Direct Deployment without Branch Switching (recommended for now)

This approach avoids switching branches locally, which prevents issues with uncommitted changes:

1. **Build and deploy in one step**

   ```bash
   ./push_site_to_ghpages.sh "Update documentation"
   ```

   This script:
   - Builds the documentation
   - Creates the gh-pages branch remotely if it doesn't exist
   - Clones the gh-pages branch to a temporary directory
   - Copies your built site to this temporary directory
   - Commits and pushes the changes
   - Cleans up without touching your working directory

2. **Deploy an existing site**

   If you've already built the site and just want to deploy:

   ```bash
   ./push_existing_site.sh "Deploy existing site"
   ```

3. **Enable GitHub Pages**

   - Go to your repository on GitHub
   - Navigate to Settings > Pages
   - Under "Source", select "Deploy from a branch"
   - Select the "gh-pages" branch and "/ (root)" folder

### Option 3: Manual Deployment with Branch Switching

This approach involves manually building the documentation and pushing it to the `gh-pages` branch.

1. **Build the documentation**

   ```bash
   mkdocs build
   ```

   This will generate the static site in the `site/` directory.

2. **Deploy using the script**

   Use the provided `deploy_docs.sh` script:

   ```bash
   ./deploy_docs.sh "Your commit message"
   ```

   This script:
   - Builds the documentation
   - Stashes any uncommitted changes to avoid conflicts
   - Switches to the gh-pages branch (or creates it if it doesn't exist)
   - Replaces the content with the new build
   - Commits and pushes the changes
   - Switches back to your original branch
   - Restores your uncommitted changes

   **Note:** It's still best practice to commit your changes before deploying.

3. **Deploy manually**

   Or perform the steps manually:

   ```bash
   # Build the docs
   mkdocs build
   
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
   ```

## Troubleshooting

### Uncommitted Changes Error

If you see an error like this when deploying:

```
error: Your local changes to the following files would be overwritten by checkout:
        [list of files]
Please commit your changes or stash them before you switch branches.
Aborting
```

This means you have uncommitted changes in your working directory. You have several options:

1. **Use the direct deployment approach** (recommended):
   ```bash
   ./push_site_to_ghpages.sh "Your message here"
   ```
   This avoids branch switching altogether.

2. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Your message here"
   ```
   Then run the deployment script again.

2. **Stash your changes**:
   ```bash
   git stash
   ```
   Run the deployment script, then restore your changes with:
   ```bash
   git stash pop
   ```

3. **Use the updated deploy_docs.sh script** which automatically handles stashing and restoring your changes.

### 404 Page Not Found

If you see a 404 error when visiting your GitHub Pages site:

1. Make sure you've enabled GitHub Pages in your repository settings
2. Check that your branch is set correctly (either `gh-pages` or the branch you specified)
3. Verify that the site is being built correctly by checking the Actions tab
4. Ensure your repository is public, or that GitHub Pages is enabled for private repositories in your organization

### CSS/JS Not Loading

If your site loads but appears unstyled:

1. Check the path in your `mkdocs.yml` for CSS and JavaScript files
2. Ensure the `site_url` in your `mkdocs.yml` is set correctly
3. Add `use_directory_urls: false` to your `mkdocs.yml` file

## Best Practices

1. **Always preview locally** before deploying:
   ```bash
   mkdocs serve
   ```

2. **Use version control** to track changes to your documentation

3. **Automate deployment** when possible using GitHub Actions

4. **Include a .nojekyll file** in your GitHub Pages site to prevent Jekyll processing

5. **Set up branch protection** for your `gh-pages` branch to prevent accidental deletions

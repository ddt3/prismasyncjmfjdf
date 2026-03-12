# Release Process for prismasyncjmfjdf

This directory contains automated scripts for releasing new versions of the prismasyncjmfjdf module to GitHub.

## Quick Start

### Windows (PowerShell)

```powershell
# Set your GitHub token (one-time setup per session)
$env:GITHUB_TOKEN = "your_github_token"

# Run the release script
.\release.ps1

# Or perform a dry run (checks and builds, but doesn't create release)
.\release.ps1 -DryRun
```

### Linux/macOS (Bash)

```bash
# Set your GitHub token
export GITHUB_TOKEN="your_github_token"

# Run the Python release script
python3 release_version.py

# Or perform a dry run (checks and builds, but doesn't create release)
python3 release_version.py --dry-run
```

## Prerequisites

1. **GitHub Personal Access Token**
   
   **Option A: Fine-Grained Token (Recommended)**
   - Go to https://github.com/settings/tokens?type=beta
   - Click "Generate new token"
   - Configure:
     - Repository access: Select only `ddt3/prismasyncjmfjdf`
     - Permissions needed:
       - **Contents**: Read and write (create releases, upload assets)
       - **Workflows**: Read and write (manage workflows)
   - Copy the token
   
   **Option B: Classic Token (Less Secure)**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo` and `workflows`
   - Copy the token

2. **Python Dependencies**
   - `build` package (usually included in modern Python)
   - `requests` library (install via `pip install requests`)
   - `tomllib` (Python 3.11+) or `tomli` for older versions

3. **Python Build Tools**
   ```bash
   python -m pip install build setuptools requests
   ```

## Release Checklist

Before running the release scripts:

- [ ] Update the version number in `pyproject.toml`
- [ ] Commit changes to your main branch
- [ ] Push changes to GitHub
- [ ] Have your GitHub Personal Access Token ready

**Note:** The release script will automatically check that:
- All local changes are committed
- Your local branch is up to date with the remote repository

## What the Scripts Do

### 1. Version Checking
- Reads the current version from `pyproject.toml`
- Fetches the latest release tag from GitHub
- Compares versions and aborts if no change detected

### 2. Building
- Runs `python -m build .` to build the module
- Creates a wheel file (`.whl`) in the `dist/` directory

### 3. Wheel File Renaming
- Renames the wheel file to remove version information
- Example: `prismasyncjmfjdf-0.9.6-py3-none-any.whl` → `prismasyncjmfjdf-py3-none-any.whl`
- This makes the filename stable across versions

### 4. GitHub Release
- Creates a new release with tag `v<version>`
- Uploads the renamed wheel file as a release asset
- Creates a release notes entry

## Dry Run Mode

The release scripts support a `--dry-run` option to test the entire release process without actually creating a GitHub release. This is useful for:

- Validating that version checks pass
- Testing the build process
- Verifying the wheel file is generated correctly
- Checking git status without side effects

### Using Dry Run

**Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN = "your_token"
.\release.ps1 -DryRun
```

**Linux/macOS (Bash):**
```bash
export GITHUB_TOKEN="your_token"
bash release.sh --dry-run
```

**Direct Python:**
```bash
python release_version.py --dry-run
```

In dry run mode, the script will:
- Check git status (no changes allowed)
- Verify branch is up to date with remote
- Validate version has changed
- Build the wheel file
- Rename the wheel file
- **NOT** create a GitHub release
- **NOT** upload assets

Example output:
```
Step 5: Renaming wheel file...
Renamed wheel: prismasyncjmfjdf-0.9.6-py3-none-any.whl → prismasyncjmfjdf-py3-none-any.whl

DRY RUN: Skipping actual GitHub release creation
   Would create release: v0.9.6
   Would upload asset: prismasyncjmfjdf-py3-none-any.whl

Release completed successfully!
```

## Script Details

### `release_version.py`
The main Python script that:
- Parses `pyproject.toml` using `tomllib`
- Communicates with GitHub API via `requests`
- Builds the module
- Manages the release process

**Usage:**
```bash
python release_version.py
```

**Environment Variables:**
- `GITHUB_TOKEN`: Required for creating releases and uploading assets

**Exit Codes:**
- `0`: Success
- `1`: Failed (check error messages)

### `release.ps1`
PowerShell wrapper that:
- Makes it easy to set and pass GitHub token
- Provides help documentation
- Handles cross-platform concerns
- Shows user-friendly formatting

**Usage:**
```powershell
# Show help
.\release.ps1 -Help

# Run with token from environment
$env:GITHUB_TOKEN = "token"
.\release.ps1

# Run with inline token
.\release.ps1 -GitHubToken "token"
```

## Examples

### Example 1: Release on Windows PowerShell

```powershell
# In VS Code terminal (PowerShell)
$env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
.\release.ps1

# Output:
# ============================================================
# PRISMAsync Python Module Release Script
# ============================================================
#
# Step 1: Checking version...
# Current version in pyproject.toml: 0.9.7
#
# Step 2: Checking GitHub releases...
# Latest release on GitHub: 0.9.6
#
# Step 3: Comparing versions...
# Version changed: 0.9.6 → 0.9.7
#
# Building module...
# Build completed successfully
#
# Step 5: Renaming wheel file...
# Renamed wheel: prismasyncjmfjdf-0.9.7-py3-none-any.whl → prismasyncjmfjdf-py3-none-any.whl
#
# Creating release v0.9.7...
# Release created: https://github.com/ddt3/prismasyncjmfjdf/releases/tag/v0.9.7
#
# Uploading wheel file...
# Asset uploaded: prismasyncjmfjdf-py3-none-any.whl
#
# Release completed successfully!
# Release URL: https://github.com/ddt3/prismasyncjmfjdf/releases/tag/v0.9.7
```

### Example 2: Release from Command Line

```bash
# Set token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Run release
python release_version.py
```

## Troubleshooting

### "You have uncommitted changes"
**Reason:** The release script detected uncommitted changes in your working directory
**Solution:** Commit or stash your changes before releasing
```bash
# Commit your changes
git add .
git commit -m "Your commit message"

# Or stash them for later
git stash
```

### "Local branch is not up to date with remote"
**Reason:** Your local commits haven't been pushed to GitHub yet
**Solution:** Push your local changes to the remote repository
```bash
git push origin main  # or your branch name
```

### "GITHUB_TOKEN environment variable not set"
**Solution:** Set your token before running the script
```powershell
$env:GITHUB_TOKEN = "your_token"
```

### "Version not changed"
**Solution:** Update the version number in `pyproject.toml` before releasing
```toml
[project]
version = "0.9.7"  # Change this from 0.9.6
```

### "Build failed"
**Solution:** Ensure all dependencies are installed and Python can import the module
```bash
python -m pip install build setuptools requests
cd C:\path\to\prismasyncjmfjdf
python -m build .
```

### "Failed to create release: 422"
**Reason:** Release with this tag already exists
**Solution:** Either:
- Use a different version number, or
- Delete the release on GitHub and run again

### "Failed to upload asset"
**Reason:** File already exists or GitHub API issues
**Solution:**
- Check GitHub API rate limits
- Ensure token has `repo` scope
- Try again in a few moments

### "Failed to create release: 403" or "Resource not accessible"
**Reason:** Token doesn't have required permissions
**Solution for fine-grained tokens:**
- Go to https://github.com/settings/tokens?type=beta
- Edit the token
- Ensure **Repository access** includes `ddt3/prismasyncjmfjdf` (not just "All repositories")
- Check **Repository permissions**:
  - **Contents**: `Read and write` ✓ (REQUIRED for releases)
  - **Workflows**: `Read and write` ✓ (REQUIRED)
  - **Metadata**: `Read-only` (auto-included)
- Click "Update token"
- Copy the new token and try again

**For classic tokens:**
- Go to https://github.com/settings/tokens
- Edit the token
- Ensure both `repo` and `workflows` scopes are checked
- Click "Update"
- Try again

## GitHub Token Security

**Important:** Never commit your GitHub token to version control!

Best practices:
- Use environment variables (set temporarily per session)
- Don't pass token as command-line argument in scripts
- Regenerate token if compromised
- Use fine-grained tokens limited to specific repositories
- Set reasonable expiration dates

### Fine-Grained Token Setup (Recommended)

1. Go to https://github.com/settings/tokens?type=beta
2. Click "Generate new token"
3. Fill in:
   - **Token name:** `prismasyncjmfjdf-release`
   - **Expiration:** 30-90 days (recommended)
   - **Repository access:** Select "Only select repositories"
   - **Select repository:** `ddt3/prismasyncjmfjdf`
4. Under "Repository permissions", set:
   - **Contents:** `Read and write` ✓ (REQUIRED - for creating releases and uploading assets)
   - **Workflows:** `Read and write` ✓ (REQUIRED - for managing workflows)
   - **Metadata:** `Read-only` (auto-included, for repository info)
5. Click "Generate token"
6. Copy and save the token securely

**Important:** Both "Contents" and "Workflows" **must** be set to "Read and write" or the release will fail with a 403 error.

### Classic Token Setup

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (full control of private repositories)
   - `workflows` (update GitHub Action workflows)
4. Click "Generate token"
5. Copy and save the token

## Alternative: Using GitHub CLI

If you prefer using the GitHub CLI (`gh`), you can:

```bash
# Install GitHub CLI
# https://cli.github.com/

# Authenticate
gh auth login

# Then run the Python script (it will use gh auth)
python release_version.py
```

The script currently uses the `requests` library, but could be extended to auto-detect GitHub CLI auth.

## Integration with CI/CD

To integrate this into GitHub Actions:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install build requests
      - run: python release_version.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the script output for error messages
3. Check GitHub API status page
4. Verify your token has correct permissions

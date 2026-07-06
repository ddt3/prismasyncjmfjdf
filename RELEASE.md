# Release Process for prismasyncjmfjdf

This repository includes automation for publishing a new GitHub release of prismasyncjmfjdf.

The primary release path is:

- Windows PowerShell script: release.ps1
- GitHub interactions through GitHub CLI (gh)

## Quick Start

### Windows (PowerShell)

```powershell
# Optional if gh is already authenticated:
$env:GITHUB_TOKEN = "your_github_token"

# Run full release
.\release.ps1

# Dry run (checks + build, no release creation)
.\release.ps1 -DryRun
```

### Linux/macOS (Bash)

```bash
# Python release flow (legacy / alternate path)
export GITHUB_TOKEN="your_github_token"
python3 release_version.py

# Dry run
python3 release_version.py --dry-run
```

## Prerequisites

1. GitHub CLI (gh)
  - Install: https://cli.github.com/
  - Authenticate once:
    ```bash
    gh auth login
    ```
  - Or provide GITHUB_TOKEN in environment for the session.

2. Python build support
  - Python 3.11+
  - Build backend dependencies available for:
    ```bash
    python -m build .
    ```

3. Repository state
  - Working tree must be clean
  - Local branch must match origin/<current-branch>
  - Version in pyproject.toml must be greater than latest GitHub release

## What release.ps1 Does

The script runs these steps in order:

1. Tool checks
  - Verifies git, python, and gh are available
  - Verifies either gh auth is valid or GITHUB_TOKEN is set

2. Git safety checks
  - Fails if there are uncommitted changes
  - Runs git fetch origin
  - Fails if local HEAD differs from origin/<current-branch>

3. Version checks
  - Reads [project].version from pyproject.toml
  - Reads latest release tag from GitHub using:
    - gh api repos/ddt3/prismasyncjmfjdf/releases/latest --jq '.tag_name'
  - Fails if current version is not greater than latest release

4. Build
  - Runs python -m build .
  - Finds the newest .whl file in dist/

5. Release creation
  - Uses gh release create to create tag v<version>
  - Uploads the wheel file directly as an asset
  - Keeps the original wheel filename (no rename step)

## Dry Run Behavior

Run:

```powershell
.\release.ps1 -DryRun
```

Dry run will:

- Perform all tool, git, and version checks
- Build the wheel
- Show which tag and asset would be used
- Not create a GitHub release
- Not upload assets

## Usage

### release.ps1

```powershell
# Help
.\release.ps1 -Help

# Use existing gh auth (recommended)
.\release.ps1

# Provide token via env var
$env:GITHUB_TOKEN = "ghp_xxx"
.\release.ps1

# Provide token inline
.\release.ps1 -GitHubToken "ghp_xxx"

# Dry run
.\release.ps1 -DryRun
```

## Troubleshooting

### You have uncommitted changes

Reason: The script enforces a clean working tree.

Fix:

```bash
git add .
git commit -m "Your commit message"
```

### Local branch is not up to date with origin

Reason: Local HEAD differs from origin/<branch>.

Fix:

```bash
git push origin <branch>
```

### Neither gh auth nor GITHUB_TOKEN is available

Reason: The script could not authenticate GitHub operations.

Fix one of:

```bash
gh auth login
```

or

```powershell
$env:GITHUB_TOKEN = "your_token"
```

### Version must be greater than latest release

Reason: pyproject.toml version is unchanged or lower than latest tag.

Fix: Increase [project].version before running release.

### Build failed

Reason: Python build dependencies or packaging configuration issue.

Fix:

```bash
python -m pip install --upgrade build setuptools
python -m build .
```

### gh release create failed because tag already exists

Reason: A release/tag for v<version> already exists.

Fix:

- bump version and retry, or
- delete the existing tag/release and retry

## Security Notes

- Never commit tokens to source control.
- Prefer gh auth login for local development.
- If using GITHUB_TOKEN, set it only for the active shell session.
- Use least-privilege fine-grained tokens scoped to this repository.

## Support

If release fails:

1. Re-run with dry run and capture output
2. Verify git status and branch sync
3. Verify pyproject.toml version bump
4. Verify gh auth status

# Release automation script wrapper for prismasyncjmfjdf
# Usage: .\release.ps1

param(
    [string]$GitHubToken = $null,
    [switch]$DryRun = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host @"
PRISMAsync Python Module Release Script
========================================

Usage: .\release.ps1 [-GitHubToken <token>] [-DryRun] [-Help]

Options:
  -GitHubToken <token>  GitHub Personal Access Token (or set GITHUB_TOKEN environment variable)
  -DryRun               Perform all checks and build, but don't create actual release
  -Help                 Show this help message

Setup Instructions:
  1. Create a GitHub Personal Access Token:
     - Fine-grained (recommended): https://github.com/settings/tokens?type=beta
       * Select repository: ddt3/prismasyncjmfjdf
       * Permissions: Contents (read/write), Workflows (read/write)
     - Classic: https://github.com/settings/tokens
       * Scopes: repo, workflows
     - Copy the token

  2. Run this script with your token:
     `$env:GITHUB_TOKEN = "your_token_here"`
     .\release.ps1

  Or pass it directly:
     .\release.ps1 -GitHubToken "your_token_here"

Requirements:
  - Python 3 with 'build' package
  - requests library
  - pyproject.toml with updated version number

Release Checklist:
  1. Update version in pyproject.toml
  2. Commit and push changes to main branch
  3. Run this script with a valid GitHub token
  4. Script will:
     - Check version changed from latest release
     - Build the wheel file
     - Rename wheel to remove version info
     - Create GitHub release with tag v<version>
     - Upload wheel as release asset

"@
    exit 0
}

# Get current directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $scriptDir

try {
    # Check git status and upstream
    Write-Host "Checking git status..." -ForegroundColor Cyan
    
    # Check for uncommitted changes
    $gitStatus = git status --porcelain 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Not in a git repository or git command failed" -ForegroundColor Yellow
    } elseif ($gitStatus) {
        Write-Host "❌ You have uncommitted changes:" -ForegroundColor Red
        Write-Host $gitStatus
        Write-Host ""
        Write-Host "Please commit or stash your changes before releasing:" -ForegroundColor Yellow
        Write-Host "  git add ."
        Write-Host "  git commit -m 'message'"
        exit 1
    } else {
        Write-Host "✓ Working directory is clean" -ForegroundColor Green
    }
    
    # Fetch latest from remote
    git fetch 2>$null
    
    # Get current branch
    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($LASTEXITCODE -eq 0) {
        # Check if branch is up to date with remote
        $localCommit = git rev-parse HEAD 2>$null
        $remoteCommit = git rev-parse "origin/$currentBranch" 2>$null
        
        if ($remoteCommit -and $localCommit -ne $remoteCommit) {
            Write-Host "❌ Local branch is not up to date with remote" -ForegroundColor Red
            Write-Host "Please push your changes to GitHub:"
            Write-Host "  git push origin $currentBranch"
            exit 1
        } elseif ($remoteCommit) {
            Write-Host "✓ Local branch is up to date with remote" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    
    # Activate virtual environment
    $venvPath = Join-Path $scriptDir ".venv"
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    
    if (Test-Path $activateScript) {
        Write-Host "Activating virtual environment..." -ForegroundColor Cyan
        & $activateScript
    } else {
        Write-Host "⚠️ Virtual environment not found at $venvPath" -ForegroundColor Yellow
        Write-Host "Install dependencies with: python -m pip install build requests" -ForegroundColor Yellow
    }
    
    # Set up GitHub token
    if ($GitHubToken) {
        $env:GITHUB_TOKEN = $GitHubToken
    }
    
    if (-not $env:GITHUB_TOKEN) {
        Write-Host "❌ GITHUB_TOKEN not set" -ForegroundColor Red
        Write-Host ""
        Write-Host "Set your GitHub token first:"
        Write-Host ""
        Write-Host "  `$env:GITHUB_TOKEN = 'your_token_here'"
        Write-Host "  .\release.ps1"
        Write-Host ""
        Write-Host "Or run: .\release.ps1 -Help" -ForegroundColor Cyan
        exit 1
    }
    
    # Run the Python release script
    Write-Host "Starting release process..." -ForegroundColor Cyan
    Write-Host ""
    
    $pythonArgs = @("release_version.py")
    if ($DryRun) {
        $pythonArgs += "--dry-run"
        Write-Host "🔄 DRY RUN MODE - No release will be created" -ForegroundColor Yellow
        Write-Host ""
    }
    
    python @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Release completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Release failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
}
finally {
    Pop-Location
}

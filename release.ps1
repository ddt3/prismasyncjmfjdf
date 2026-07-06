# Release automation script for prismasyncjmfjdf
# Usage: .\release.ps1

param(
    [string]$GitHubToken = $null,
    [switch]$DryRun = $false,
    [switch]$Help = $false
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n$Message" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

function Get-PyProjectVersion {
    param([string]$PyProjectPath)

    if (-not (Test-Path $PyProjectPath)) {
        Fail "pyproject.toml not found at $PyProjectPath"
    }

    $inProjectSection = $false
    foreach ($line in Get-Content -Path $PyProjectPath) {
        if ($line -match '^\s*\[project\]\s*$') {
            $inProjectSection = $true
            continue
        }
        if ($inProjectSection -and $line -match '^\s*\[') {
            break
        }
        if ($inProjectSection -and $line -match '^\s*version\s*=\s*"([^"]+)"') {
            return $matches[1]
        }
    }

    Fail "Could not find [project].version in pyproject.toml"
}

function Get-LatestReleaseVersion {
    param([string]$Repository)

    $output = gh api "repos/$Repository/releases/latest" --jq '.tag_name' 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $output) {
        return $null
    }

    return ($output.Trim()) -replace '^[vV]', ''
}

if ($Help) {
    Write-Host @"
PRISMAsync Python Module Release Script
=======================================

Usage: .\release.ps1 [-GitHubToken <token>] [-DryRun] [-Help]

Options:
  -GitHubToken <token>  GitHub token (or set GITHUB_TOKEN environment variable)
  -DryRun               Perform checks and build; do not create a release
  -Help                 Show this help message

What this script does:
  1. Validates clean git working tree
  2. Validates local branch is in sync with origin
  3. Reads version from pyproject.toml
  4. Checks latest GitHub release using gh
  5. Builds the wheel with python -m build .
  6. Creates release with gh and uploads the original wheel filename
"@
    exit 0
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = "ddt3/prismasyncjmfjdf"

Push-Location $scriptDir
try {
    Write-Host "============================================================" -ForegroundColor DarkCyan
    Write-Host "PRISMAsync Python Module Release Script" -ForegroundColor DarkCyan
    Write-Host "============================================================" -ForegroundColor DarkCyan

    if ($GitHubToken) {
        $env:GITHUB_TOKEN = $GitHubToken
    }

    Write-Step "Step 0: Checking required tools..."
    foreach ($tool in @("git", "python", "gh")) {
        $null = Get-Command $tool -ErrorAction SilentlyContinue
        if (-not $?) {
            Fail "Required tool '$tool' is not available on PATH"
        }
    }

    gh auth status | Out-Null
    $ghAuthed = ($LASTEXITCODE -eq 0)
    if (-not $ghAuthed -and -not $env:GITHUB_TOKEN) {
        Fail "Neither gh authentication nor GITHUB_TOKEN is available. Run 'gh auth login' or set GITHUB_TOKEN."
    }

    Write-Step "Step 1: Checking git status..."
    $gitStatus = git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        Fail "Not in a git repository or git status failed"
    }
    if ($gitStatus) {
        Write-Host $gitStatus
        Fail "You have uncommitted changes. Commit or stash before releasing."
    }
    Write-Host "[OK] Working directory is clean" -ForegroundColor Green

    git fetch origin
    if ($LASTEXITCODE -ne 0) {
        Fail "Failed to fetch from origin"
    }

    $currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
    if (-not $currentBranch) {
        Fail "Could not determine current branch"
    }

    $localCommit = (git rev-parse HEAD).Trim()
    $remoteCommit = (git rev-parse "origin/$currentBranch" 2>$null).Trim()
    if (-not $remoteCommit) {
        Fail "Could not resolve origin/$currentBranch"
    }

    if ($localCommit -ne $remoteCommit) {
        Fail "Local branch '$currentBranch' is not up to date with origin/$currentBranch"
    }
    Write-Host "[OK] Branch '$currentBranch' is up to date with origin" -ForegroundColor Green

    Write-Step "Step 2: Reading project version..."
    $pyprojectPath = Join-Path $scriptDir "pyproject.toml"
    $currentVersion = Get-PyProjectVersion -PyProjectPath $pyprojectPath
    Write-Host "Current version in pyproject.toml: $currentVersion"

    Write-Step "Step 3: Checking latest release on GitHub..."
    $latestVersion = Get-LatestReleaseVersion -Repository $repo
    if ($latestVersion) {
        Write-Host "Latest release on GitHub: $latestVersion"
        [version]$curr = $currentVersion
        [version]$latest = $latestVersion
        if ($curr -le $latest) {
            Fail "Version must be greater than latest release ($latestVersion)."
        }
        Write-Host "[OK] Version changed: $latestVersion -> $currentVersion" -ForegroundColor Green
    } else {
        Write-Host "No existing releases found on GitHub"
    }

    Write-Step "Step 4: Building wheel..."
    python -m build .
    if ($LASTEXITCODE -ne 0) {
        Fail "Build failed"
    }

    $distDir = Join-Path $scriptDir "dist"
    $wheels = Get-ChildItem -Path $distDir -Filter "*.whl" | Sort-Object LastWriteTime -Descending
    if (-not $wheels -or $wheels.Count -eq 0) {
        Fail "No wheel file found in dist/"
    }
    $wheelPath = $wheels[0].FullName
    $wheelName = $wheels[0].Name
    Write-Host "[OK] Built wheel: $wheelName" -ForegroundColor Green

    $tag = "v$currentVersion"

    if ($DryRun) {
        Write-Step "Step 5: Dry run summary"
        Write-Host "[DRY-RUN] Would create release: $tag" -ForegroundColor Yellow
        Write-Host "[DRY-RUN] Would upload asset: $wheelName" -ForegroundColor Yellow
        Write-Host "`nRelease checks and build completed successfully." -ForegroundColor Green
        exit 0
    }

    Write-Step "Step 5: Creating GitHub release with gh..."
    gh release create $tag $wheelPath --repo $repo --title "Release $tag" --notes "Release $tag of prismasyncjmfjdf"
    if ($LASTEXITCODE -ne 0) {
        Fail "Failed to create GitHub release"
    }

    Write-Host "`n[SUCCESS] Release completed successfully!" -ForegroundColor Green
    Write-Host "Release URL: https://github.com/$repo/releases/tag/$tag"
}
finally {
    Pop-Location
}

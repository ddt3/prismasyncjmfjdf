#!/bin/bash
# Release automation script for prismasyncjmfjdf (Bash version)
# Usage: bash release.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Show help
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    cat << 'EOF'
PRISMAsync Python Module Release Script
========================================

Usage: bash release.sh [OPTIONS]

Options:
  -h, --help          Show this help message
  -t, --token TOKEN   GitHub Personal Access Token
  -d, --dry-run       Perform all checks and build, but don't create actual release

Environment Variables:
  GITHUB_TOKEN        GitHub Personal Access Token (required if -t not provided)

Setup Instructions:
  1. Create a GitHub Personal Access Token:
     - Fine-grained (recommended): https://github.com/settings/tokens?type=beta
       * Select repository: ddt3/prismasyncjmfjdf
       * Permissions: Contents (read/write), Workflows (read/write)
     - Classic: https://github.com/settings/tokens
       * Scopes: repo, workflows
     - Copy the token

  2. Run this script:
     export GITHUB_TOKEN="your_token_here"
     bash release.sh

Requirements:
  - Python 3.11+ (for tomllib)
  - requests library (or urllib fallback)
  - build package
  - pyproject.toml with updated version number

Release Checklist:
  1. Update version in pyproject.toml
  2. Commit and push changes
  3. Run: bash release.sh

EOF
    exit 0
fi

# Parse arguments
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
DRY_RUN=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Check GitHub token
if [[ -z "$GITHUB_TOKEN" ]]; then
    echo -e "${RED}❌ GITHUB_TOKEN not set${NC}"
    echo ""
    echo "Set your GitHub token:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    echo "  bash release.sh"
    echo ""
    exit 1
fi

# Activate virtual environment if it exists
VENV_PATH="${SCRIPT_DIR}/venv"
if [[ -f "${VENV_PATH}/bin/activate" ]]; then
    echo -e "${CYAN}Activating virtual environment...${NC}"
    source "${VENV_PATH}/bin/activate"
elif [[ -f "${SCRIPT_DIR}/.venv/bin/activate" ]]; then
    echo -e "${CYAN}Activating virtual environment...${NC}"
    source "${SCRIPT_DIR}/.venv/bin/activate"
fi

# Run the Python release script
echo -e "${CYAN}Starting release process...${NC}"
echo ""

# Check git status and upstream
echo -e "${CYAN}Checking git status...${NC}"

# Check for uncommitted changes
if ! git status --porcelain | grep -q .; then
    echo -e "${GREEN}✓ Working directory is clean${NC}"
else
    echo -e "${RED}❌ You have uncommitted changes:${NC}"
    git status --short
    echo ""
    echo -e "${CYAN}Please commit or stash your changes before releasing:${NC}"
    echo "  git add ."
    echo "  git commit -m 'message'"
    exit 1
fi

# Fetch latest from remote
git fetch > /dev/null 2>&1

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [[ ! -z "$CURRENT_BRANCH" ]]; then
    LOCAL_COMMIT=$(git rev-parse HEAD 2>/dev/null)
    REMOTE_COMMIT=$(git rev-parse "origin/$CURRENT_BRANCH" 2>/dev/null)
    
    if [[ ! -z "$REMOTE_COMMIT" ]] && [[ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]]; then
        echo -e "${RED}❌ Local branch is not up to date with remote${NC}"
        echo "Please push your changes to GitHub:"
        echo "  git push origin $CURRENT_BRANCH"
        exit 1
    elif [[ ! -z "$REMOTE_COMMIT" ]]; then
        echo -e "${GREEN}✓ Local branch is up to date with remote${NC}"
    fi
fi

echo ""

# Activate virtual environment if it exists
VENV_PATH="${SCRIPT_DIR}/venv"
if [[ -f "${VENV_PATH}/bin/activate" ]]; then
    echo -e "${CYAN}Activating virtual environment...${NC}"
    source "${VENV_PATH}/bin/activate"
elif [[ -f "${SCRIPT_DIR}/.venv/bin/activate" ]]; then
    echo -e "${CYAN}Activating virtual environment...${NC}"
    source "${SCRIPT_DIR}/.venv/bin/activate"
fi

echo -e "${CYAN}Running release script...${NC}"
echo ""

python3 release_version.py $DRY_RUN

if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ Release completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Release failed${NC}"
    exit 1
fi

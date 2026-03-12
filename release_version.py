#!/usr/bin/env python3
"""
Release automation script for prismasyncjmfjdf
Handles version checking, release creation, building, and uploading assets
"""

import os
import sys
import re
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple
import tomllib

# Try to use requests, fall back to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

# Configuration
GITHUB_REPO = "ddt3/prismasyncjmfjdf"
GITHUB_API_BASE = "https://api.github.com"
PROJECT_NAME = "prismasyncjmfjdf"
PROJECT_ROOT = Path(__file__).parent.resolve()
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
DIST_DIR = PROJECT_ROOT / "dist"


def get_pyproject_version() -> str:
    """Extract version from pyproject.toml"""
    with open(PYPROJECT_PATH, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string to tuple of ints for comparison"""
    parts = version_str.split(".")
    return tuple(int(p) for p in parts[:3])


def check_git_status() -> bool:
    """Check that git working directory is clean and upstream is up to date"""
    try:
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("[WARNING] Could not check git status (may not be in a git repository)")
            return True  # Don't block non-repo releases
        
        if result.stdout.strip():
            print("[ERROR] You have uncommitted changes:")
            print(result.stdout)
            print("Please commit or stash your changes before releasing:")
            print("  git add .")
            print("  git commit -m 'message'")
            return False
        
        print("[OK] Working directory is clean")
        
        # Fetch latest from remote
        subprocess.run(
            ["git", "fetch"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=10
        )
        
        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return True  # Couldn't determine branch, continue anyway
        
        current_branch = result.stdout.strip()
        
        # Check if local is up to date with remote
        local_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        remote_result = subprocess.run(
            ["git", "rev-parse", f"origin/{current_branch}"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if remote_result.returncode == 0:
            local_commit = local_result.stdout.strip()
            remote_commit = remote_result.stdout.strip()
            
            if local_commit != remote_commit:
                print(f"[ERROR] Local branch '{current_branch}' is not up to date with remote")
                print("Please push your changes to GitHub:")
                print(f"  git push origin {current_branch}")
                return False
            
            print(f"[OK] Local branch '{current_branch}' is up to date with remote")
        
        return True
        
    except Exception as e:
        print(f"[WARNING] Could not check git status: {e}")
        return True  # Don't block on git check errors


def get_latest_github_release() -> Optional[str]:
    """Get the latest release version from GitHub"""
    try:
        url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/releases/latest"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        if HAS_REQUESTS:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 404:
                print("[INFO] No previous releases found on GitHub")
                return None
            response.raise_for_status()
            data = response.json()
        else:
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print("[INFO] No previous releases found on GitHub")
                    return None
                raise
        
        tag = data.get("tag_name", "").lstrip("vV")
        return tag if tag else None
    except Exception as e:
        print(f"[ERROR] Error fetching latest release: {e}")
        return None


def check_version_changed(current_version: str, latest_version: Optional[str]) -> bool:
    """Check if version has been changed"""
    if latest_version is None:
        print(f"[OK] No previous release found. Current version: {current_version}")
        return True
    
    current = parse_version(current_version)
    latest = parse_version(latest_version)
    
    if current > latest:
        print(f"[OK] Version changed: {latest_version} -> {current_version}")
        return True
    elif current == latest:
        print(f"[ERROR] Version not changed: still {current_version}")
        return False
    else:
        print(f"[ERROR] Version decreased: {latest_version} -> {current_version}")
        return False


def build_module() -> str:
    """Build the module using python -m build"""
    print("\n[BUILD] Building module...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "build", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"[ERROR] Build failed:\n{result.stderr}")
            sys.exit(1)
        
        print("[OK] Build completed successfully")
        
        # Find the wheel file
        wheel_files = list(DIST_DIR.glob("*.whl"))
        if not wheel_files:
            print("[ERROR] No wheel file found in dist/")
            sys.exit(1)
        
        wheel_path = wheel_files[0]
        return str(wheel_path)
    except Exception as e:
        print(f"[ERROR] Build failed: {e}")
        sys.exit(1)


def get_renamed_wheel(wheel_path: str) -> str:
    """
    Rename wheel file to remove version information
    e.g., prismasyncjmfjdf-0.9.6-py3-none-any.whl → prismasyncjmfjdf-py3-none-any.whl
    """
    wheel_file = Path(wheel_path)
    
    # Wheel filename format: {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
    # We want to remove the version part
    match = re.match(
        r"^(.+?)-\d+(?:\.\d+)*(?:\.\w+)*(-py\d+-none-any\.whl)$",
        wheel_file.name
    )
    
    if not match:
        print(f"[WARNING] Could not parse wheel filename: {wheel_file.name}")
        return wheel_path
    
    new_name = match.group(1) + match.group(2)
    new_path = wheel_file.parent / new_name
    
    if wheel_file != new_path:
        shutil.move(str(wheel_file), str(new_path))
        print(f"[OK] Renamed wheel: {wheel_file.name} -> {new_name}")
        return str(new_path)
    
    return wheel_path


def create_github_release(
    version: str,
    wheel_path: str,
    github_token: Optional[str] = None,
    dry_run: bool = False
) -> bool:
    """Create a release on GitHub and upload the wheel file"""
    if dry_run:
        print("\n[DRY-RUN] Skipping actual GitHub release creation")
        print(f"   Would create release: v{version}")
        print(f"   Would upload asset: {Path(wheel_path).name}")
        return True
    if github_token is None:
        github_token = os.environ.get("GITHUB_TOKEN")
    
    if not github_token:
        print("\n[ERROR] GITHUB_TOKEN environment variable not set")
        print("Please set GITHUB_TOKEN to create releases:")
        print("  $env:GITHUB_TOKEN = 'your_token'")
        return False
    
    tag = f"v{version}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Create release
    print(f"\n[RELEASE] Creating release {tag}...")
    release_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/releases"
    
    release_data = {
        "tag_name": tag,
        "name": f"Release {tag}",
        "body": f"Release {tag} of prismasyncjmfjdf",
        "draft": False,
        "prerelease": False
    }
    
    try:
        # Create release
        if HAS_REQUESTS:
            response = requests.post(
                release_url,
                json=release_data,
                headers=headers,
                timeout=10
            )
            status_code = response.status_code
            response_data = response.json() if response.text else {}
        else:
            req = urllib.request.Request(
                release_url,
                data=json.dumps(release_data).encode(),
                headers=headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    response_data = json.loads(response.read().decode())
                    status_code = response.code
            except urllib.error.HTTPError as e:
                response_data = json.loads(e.read().decode()) if e.fp else {}
                status_code = e.code
        
        if status_code == 422:
            # Release already exists
            print(f"[INFO] Release {tag} already exists, retrieving existing release...")
            # Get existing release
            if HAS_REQUESTS:
                response = requests.get(
                    f"{release_url}/tags/{tag}",
                    headers=headers,
                    timeout=10
                )
                get_status = response.status_code
                response_data = response.json() if response.text else {}
            else:
                req = urllib.request.Request(f"{release_url}/tags/{tag}", headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        response_data = json.loads(response.read().decode())
                        get_status = response.code
                except urllib.error.HTTPError as e:
                    get_status = e.code
                    response_data = {}
            
            if get_status != 200:
                print(f"[ERROR] Could not create or retrieve release: {response_data}")
                return False
        elif status_code not in (201, 200):
            print(f"[ERROR] Failed to create release: {status_code}")
            print(response_data)
            return False
        
        release = response_data
        upload_url = release.get("upload_url", "").split("{")[0]  # Remove template part
        
        if not upload_url:
            print(f"[ERROR] No upload URL in release response")
            return False
        
        print(f"[OK] Release created: {release.get('html_url', 'N/A')}")
        
        # Upload wheel file
        print(f"\n[UPLOAD] Uploading wheel file...")
        wheel_path_obj = Path(wheel_path)
        
        with open(wheel_path_obj, "rb") as f:
            wheel_data = f.read()
        
        upload_headers = {
            "Authorization": f"token {github_token}",
            "Content-Type": "application/octet-stream"
        }
        
        if HAS_REQUESTS:
            response = requests.post(
                f"{upload_url}?name={wheel_path_obj.name}",
                data=wheel_data,
                headers=upload_headers,
                timeout=30
            )
            upload_status = response.status_code
        else:
            req = urllib.request.Request(
                f"{upload_url}?name={wheel_path_obj.name}",
                data=wheel_data,
                headers=upload_headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    upload_status = response.code
            except urllib.error.HTTPError as e:
                upload_status = e.code
        
        if upload_status not in (201, 200):
            print(f"[ERROR] Failed to upload asset: {upload_status}")
            return False
        
        print(f"[OK] Asset uploaded: {wheel_path_obj.name}")
        print(f"\n[SUCCESS] Release completed successfully!")
        print(f"Release URL: {release.get('html_url', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating release: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main release workflow"""
    # Parse command-line arguments
    dry_run = "--dry-run" in sys.argv
    
    print("=" * 60)
    print("PRISMAsync Python Module Release Script")
    print("=" * 60)
    
    if dry_run:
        print("\n[DRY-RUN] No actual release will be created")
    
    # Step 0: Check git status
    print("\n[STEP 0] Checking git status...")
    if not check_git_status():
        print("\n[ERROR] Aborting: Git status check failed")
        sys.exit(1)
    print("\n[STEP 1] Checking version...")
    current_version = get_pyproject_version()
    print(f"Current version in pyproject.toml: {current_version}")
    
    # Step 2: Check latest GitHub release
    print("\n[STEP 2] Checking GitHub releases...")
    latest_version = get_latest_github_release()
    
    # Step 3: Compare versions
    print("\n[STEP 3] Comparing versions...")
    if not check_version_changed(current_version, latest_version):
        print("\n[ERROR] Aborting: Version has not changed")
        sys.exit(1)
    
    # Step 4: Build module
    wheel_path = build_module()
    
    # Step 5: Rename wheel file
    print("\n[STEP 5] Renaming wheel file...")
    wheel_path = get_renamed_wheel(wheel_path)
    
    # Step 6: Create release and upload
    if not create_github_release(current_version, wheel_path, dry_run=dry_run):
        print("\n[ERROR] Release failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

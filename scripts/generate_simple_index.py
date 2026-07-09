#!/usr/bin/env python3
"""Generate a static PEP 503-style simple index for prismasyncjmfjdf releases."""

from __future__ import annotations

import html
import json
import pathlib
import urllib.request

REPO = "ddt3/prismasyncjmfjdf"
PACKAGE_NAME = "prismasyncjmfjdf"
API_URL = f"https://api.github.com/repos/{REPO}/releases"


def fetch_releases() -> list[dict]:
    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{PACKAGE_NAME}-simple-index-generator",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def wheel_links_from_releases(releases: list[dict]) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for release in releases:
        for asset in release.get("assets", []):
            name = asset.get("name", "")
            if name.endswith(".whl"):
                links.append((name, asset.get("browser_download_url", "")))
    links.sort(key=lambda item: item[0].lower())
    return links


def render_package_index(package_name: str, links: list[tuple[str, str]]) -> str:
    rows = []
    for filename, url in links:
        safe_filename = html.escape(filename)
        safe_url = html.escape(url, quote=True)
        rows.append(f'<a href="{safe_url}">{safe_filename}</a><br/>')

    body = "\n".join(rows) if rows else "No wheel files found."
    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "  <head><meta charset=\"utf-8\"><title>Simple index</title></head>\n"
        "  <body>\n"
        f"    <h1>Links for {html.escape(package_name)}</h1>\n"
        f"    {body}\n"
        "  </body>\n"
        "</html>\n"
    )


def render_root_index(package_name: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "  <head><meta charset=\"utf-8\"><title>Simple index root</title></head>\n"
        "  <body>\n"
        "    <h1>Simple index</h1>\n"
        f"    <a href=\"{package_name}/\">{package_name}</a>\n"
        "  </body>\n"
        "</html>\n"
    )


def main() -> None:
    project_root = pathlib.Path(__file__).resolve().parents[1]
    pages_root = project_root / "site"
    simple_root = pages_root / "simple"
    package_root = simple_root / PACKAGE_NAME

    package_root.mkdir(parents=True, exist_ok=True)

    releases = fetch_releases()
    links = wheel_links_from_releases(releases)

    (simple_root / "index.html").write_text(render_root_index(PACKAGE_NAME), encoding="utf-8")
    (package_root / "index.html").write_text(render_package_index(PACKAGE_NAME, links), encoding="utf-8")

    # Required to prevent Jekyll processing on GitHub Pages.
    (pages_root / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Generated index with {len(links)} wheel link(s)")


if __name__ == "__main__":
    main()

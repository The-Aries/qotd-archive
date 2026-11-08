#!/usr/bin/env python3
"""Add optional Cloudflare Web Analytics to a built GitHub Pages site."""

import json
import os
import re
from pathlib import Path

BEACON_URL = "https://static.cloudflareinsights.com/beacon.min.js"
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
SNIPPET_TOKEN_PATTERN = re.compile(
    r"""["']token["']\s*:\s*["']([A-Za-z0-9_-]{16,128})["']"""
)


def configure(site_dir: Path, setting: str) -> bool:
    """Enable analytics with either a site token or Cloudflare's full snippet."""
    if not setting:
        return False
    if TOKEN_PATTERN.fullmatch(setting):
        token = setting
    else:
        matches = SNIPPET_TOKEN_PATTERN.findall(setting) if BEACON_URL in setting else []
        if len(matches) != 1:
            raise ValueError("Invalid Cloudflare Web Analytics site token or snippet")
        token = matches[0]

    snippet = (
        f'<script type="module" defer src="{BEACON_URL}" '
        f"data-cf-beacon='{json.dumps({'token': token}, separators=(',', ':'))}'"
        "></script>"
    )
    for name in ("index.html", "add.html"):
        path = site_dir / name
        html = path.read_text(encoding="utf-8")
        if BEACON_URL in html or html.count("</body>") != 1:
            raise ValueError(f"{name}: unexpected HTML template")
        path.write_text(html.replace("</body>", f"  {snippet}\n</body>"), encoding="utf-8")
    return True


if __name__ == "__main__":
    root = Path(os.environ.get("QOTD_SITE_DIR", "_site"))
    token = os.environ.get("CLOUDFLARE_WEB_ANALYTICS_TOKEN", "").strip()
    print("Cloudflare Web Analytics:", "enabled" if configure(root, token) else "not configured")

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser(description="Update the ocsfkit Homebrew formula")
    parser.add_argument("--tap", required=True, help="owner/repo for the tap")
    parser.add_argument("--formula", required=True, help="formula path inside the tap")
    parser.add_argument("--version", required=True, help="release version without leading v")
    parser.add_argument("--archive-url", required=True, help="release source archive URL")
    args = parser.parse_args()

    archive = urllib.request.urlopen(args.archive_url, timeout=60).read()
    sha256 = hashlib.sha256(archive).hexdigest()
    api_path = f"repos/{args.tap}/contents/{args.formula}"
    current = json.loads(_gh("api", api_path))
    content = base64.b64decode(current["content"]).decode()
    content = re.sub(
        r'url "https://github\.com/pfrederiksen/ocsfkit/releases/download/v[^"]+"',
        f'url "{args.archive_url}"',
        content,
        count=1,
    )
    content = re.sub(r'sha256 "[0-9a-f]{64}"', f'sha256 "{sha256}"', content, count=1)
    encoded = base64.b64encode(content.encode()).decode()
    _gh(
        "api",
        api_path,
        "-X",
        "PUT",
        "-f",
        f"message=Update ocsfkit to {args.version}",
        "-f",
        f"content={encoded}",
        "-f",
        f"sha={current['sha']}",
    )
    print(f"Updated {args.tap}/{args.formula} to {args.version} ({sha256})")


def _gh(*args: str) -> str:
    return subprocess.check_output(("gh", *args), text=True)


if __name__ == "__main__":
    main()

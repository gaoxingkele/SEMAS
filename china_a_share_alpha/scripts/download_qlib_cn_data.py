"""Download and extract community Qlib China A-share data.

Data source: https://github.com/chenditc/investment_data
This is a community-maintained dataset in Qlib binary format.
"""

from __future__ import annotations

import argparse
import tarfile
from pathlib import Path
from urllib.request import urlopen


DEFAULT_URL = "https://github.com/chenditc/investment_data/releases/latest/download/qlib_bin.tar.gz"
DEFAULT_TARGET = Path.home() / ".qlib" / "qlib_data" / "cn_data"


def download(url: str, target: Path, chunk_size: int = 1024 * 1024) -> Path:
    """Download `url` to `target` with a simple progress indicator."""
    target.parent.mkdir(parents=True, exist_ok=True)
    archive_path = target.with_suffix(".tar.gz")

    print(f"Downloading {url} ...")
    print(f"Archive will be saved to: {archive_path}")
    with urlopen(url) as response, open(archive_path, "wb") as f:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r{downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB ({pct:.1f}%)", end="")
        print()
    return archive_path


def extract(archive_path: Path, target: Path) -> None:
    """Extract the Qlib tarball to `target`, stripping the top-level directory."""
    target.mkdir(parents=True, exist_ok=True)
    print(f"Extracting {archive_path} to {target} ...")
    with tarfile.open(archive_path, "r:gz") as tar:
        # Strip the first path component to flatten into qlib_data/cn_data.
        for member in tar.getmembers():
            parts = member.name.split("/", 1)
            if len(parts) == 1:
                continue
            member.name = parts[1]
            tar.extract(member, target)
    print("Extraction complete.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Qlib China A-share data")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL to qlib_bin.tar.gz")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help="Extract target directory")
    parser.add_argument("--keep-archive", action="store_true", help="Do not delete the tar.gz after extraction")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without downloading")
    args = parser.parse_args()

    if args.dry_run:
        print(f"Would download: {args.url}")
        print(f"Would extract to: {args.target}")
        return 0

    archive_path = download(args.url, args.target)
    extract(archive_path, args.target)
    if not args.keep_archive:
        archive_path.unlink()
        print(f"Removed archive: {archive_path}")

    print(f"Qlib data is ready at: {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

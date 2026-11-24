#!/usr/bin/env python3
"""Sync the mono README and its SVG assets into the profile repository root."""
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tsushima-readme-mono"


def main():
    source_readme = SOURCE / "README.md"
    source_assets = SOURCE / "assets"
    target_assets = ROOT / "assets"

    if not source_readme.is_file():
        raise FileNotFoundError(f"Missing source README: {source_readme}")
    if not source_assets.is_dir():
        raise FileNotFoundError(f"Missing source assets directory: {source_assets}")

    target_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_readme, ROOT / "README.md")

    assets = sorted(source_assets.glob("*.svg"))
    if not assets:
        raise FileNotFoundError(f"No SVG assets found in {source_assets}")

    for asset in assets:
        shutil.copy2(asset, target_assets / asset.name)

    print(f"Synced README.md and {len(assets)} SVG assets.")


if __name__ == "__main__":
    main()

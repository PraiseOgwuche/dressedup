#!/usr/bin/env python3
"""Download the FashionCLIP ONNX vision encoder (~350 MB, one time).

Source: Frapic/fashion-clip-onnx on Hugging Face — an ONNX export of
patrickjohncyh/fashion-clip (MIT license). Only the image tower is needed;
text prompts are not used at ingest time.
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = BACKEND_ROOT / "models" / "fashionclip"
VISION_URL = (
    "https://huggingface.co/Frapic/fashion-clip-onnx/resolve/main/vision_model.onnx"
)
FILENAME = "vision_model.onnx"
CHUNK = 1 << 20  # 1 MiB


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(".partial")
    request = urllib.request.Request(url, headers={"User-Agent": "dressedup-backend"})
    with urllib.request.urlopen(request) as response, open(partial, "wb") as out:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = response.read(CHUNK)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r{done / (1 << 20):7.1f} / {total / (1 << 20):.1f} MiB", end="")
    print()
    partial.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    target = args.dir / FILENAME
    if target.exists() and not args.force:
        print(f"Already present: {target} ({target.stat().st_size / (1 << 20):.1f} MiB)")
        return 0

    print(f"Downloading FashionCLIP vision encoder to {target}")
    download(VISION_URL, target)
    print(f"Done: {target} ({target.stat().st_size / (1 << 20):.1f} MiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

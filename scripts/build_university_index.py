#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from geo_autocomplete_internal.cli import build_university_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the ROR-based HSpace university autocomplete index."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=(
            PROJECT_ROOT
            / "input"
            / "ror_data"
            / "v2.10-2026-07-20-ror-data.json"
        ),
        help="Canonical ROR JSON dump in schema v2.1.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "dist" / "hspace" / "universities_index.csv",
    )
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(
            f"ROR source not found: {args.source}. "
            "See input/ror_data/README.md for download instructions."
        )
    organizations = build_university_file(args.source, args.output)
    print(f"Wrote {len(organizations)} HSpace universities to {args.output}")


if __name__ == "__main__":
    main()

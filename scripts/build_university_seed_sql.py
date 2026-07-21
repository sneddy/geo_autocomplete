#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from geo_autocomplete_internal.io import write_university_seed_sql
from geo_autocomplete_internal.ror import load_ror_organizations
from geo_autocomplete_internal.universities import build_university_index


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a PostgreSQL seed for the ROR university index."
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
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-release",
        default="ror-v2.10-2026-07-20",
    )
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f"ROR source not found: {args.source}")
    organizations = build_university_index(load_ror_organizations(args.source))
    write_university_seed_sql(
        organizations,
        args.output,
        source_release=args.source_release,
    )
    print(f"Wrote {len(organizations)} university rows to {args.output}")


if __name__ == "__main__":
    main()

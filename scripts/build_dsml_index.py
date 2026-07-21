#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from geo_autocomplete_internal.cli import build_dsml_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild the legacy DSML city index deterministically."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=PROJECT_ROOT / "input" / "worldcities.csv",
    )
    parser.add_argument(
        "--translations",
        type=Path,
        default=PROJECT_ROOT / "input" / "dsml_translations_ru.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "dist" / "dsml" / "cities_index_with_ru.csv",
    )
    args = parser.parse_args()
    cities = build_dsml_files(args.source, args.translations, args.output)
    print(f"Wrote {len(cities)} DSML cities to {args.output}")


if __name__ == "__main__":
    main()

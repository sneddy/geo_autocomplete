#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from geo_autocomplete_internal.cli import build_hspace_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the global research-oriented HSpace city index."
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
        default=PROJECT_ROOT / "dist" / "hspace" / "cities_index.csv",
    )
    parser.add_argument(
        "--translation-overrides",
        type=Path,
        default=PROJECT_ROOT / "input" / "hspace_translation_overrides_ru.csv",
        help="Profile-specific corrections applied after the DSML translations.",
    )
    parser.add_argument(
        "--min-population",
        type=int,
        default=50_000,
        help="Include cities at or above this population (default: 50000).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include every populated source row, ignoring the population threshold.",
    )
    args = parser.parse_args()
    if args.min_population < 0:
        parser.error("--min-population must be non-negative")
    cities = build_hspace_file(
        args.source,
        args.translations,
        args.output,
        min_population=args.min_population,
        include_all=args.all,
        translation_overrides_path=args.translation_overrides,
    )
    print(f"Wrote {len(cities)} HSpace cities to {args.output}")


if __name__ == "__main__":
    main()

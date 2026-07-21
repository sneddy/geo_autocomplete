from __future__ import annotations

from pathlib import Path

from .dsml import build_dsml_index
from .hspace import HSpaceOptions, build_hspace_index
from .io import (
    apply_translations,
    load_city_translations,
    load_world_cities,
    merge_translation_catalogs,
    write_city_index,
)
from .models import City


def build_dsml_files(
    source_path: str | Path,
    translations_path: str | Path,
    output_path: str | Path,
) -> list[City]:
    cities = load_world_cities(source_path)
    ranked = build_dsml_index(cities)
    translated = apply_translations(ranked, load_city_translations(translations_path))
    write_city_index(translated, output_path, profile="dsml")
    return translated


def build_hspace_file(
    source_path: str | Path,
    translations_path: str | Path,
    output_path: str | Path,
    *,
    min_population: int = 50_000,
    include_all: bool = False,
    translation_overrides_path: str | Path | None = None,
) -> list[City]:
    cities = load_world_cities(source_path, require_population=False)
    ranked = build_hspace_index(
        cities,
        HSpaceOptions(
            min_population=min_population,
            include_all=include_all,
        ),
    )
    catalog = load_city_translations(translations_path)
    if translation_overrides_path is not None:
        catalog = merge_translation_catalogs(
            catalog,
            load_city_translations(translation_overrides_path),
        )
    translated = apply_translations(ranked, catalog)
    write_city_index(translated, output_path, profile="hspace")
    return translated

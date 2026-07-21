"""Reusable building blocks for geographic and affiliation autocomplete."""

from .dsml import build_dsml_index
from .hspace import HSpaceOptions, build_hspace_index
from .io import (
    load_city_translations,
    load_world_cities,
    merge_translation_catalogs,
    write_city_index,
    write_university_index,
    write_university_seed_sql,
)
from .ror import load_ror_organizations
from .universities import (
    UniversitySearchIndex,
    build_university_index,
    search_universities,
    university_search_domains,
)

__all__ = [
    "HSpaceOptions",
    "UniversitySearchIndex",
    "build_dsml_index",
    "build_hspace_index",
    "build_university_index",
    "load_city_translations",
    "load_ror_organizations",
    "load_world_cities",
    "merge_translation_catalogs",
    "search_universities",
    "university_search_domains",
    "write_city_index",
    "write_university_index",
    "write_university_seed_sql",
]

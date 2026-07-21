from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

from .models import City, ResearchOrganization, TranslationCatalog
from .universities import normalize_search_text, university_search_domains


DSML_COLUMNS = (
    "priority",
    "city",
    "city_ascii",
    "lat",
    "lng",
    "country",
    "iso2",
    "iso3",
    "population",
    "city_ru",
    "country_ru",
)

HSPACE_COLUMNS = (
    "priority",
    "ranking_score",
    "ranking_reasons",
    "city",
    "city_ascii",
    "city_ru",
    "country",
    "country_ru",
    "iso2",
    "iso3",
    "admin_name",
    "capital",
    "lat",
    "lng",
    "population",
    "source_id",
)

UNIVERSITY_COLUMNS = (
    "priority",
    "ranking_score",
    "ranking_reasons",
    "ror_id",
    "display_name",
    "search_names",
    "acronyms",
    "aliases",
    "labels",
    "country",
    "country_code",
    "city",
    "admin_name",
    "geonames_id",
    "lat",
    "lng",
    "established",
    "types",
    "domains",
    "website",
)


def _required(row: dict[str, str], field: str, row_number: int) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        raise ValueError(f"Row {row_number}: required field {field!r} is empty")
    return value


def load_world_cities(
    path: str | Path, *, require_population: bool = True
) -> list[City]:
    """Load cities while preserving the vendor's source order."""

    cities: list[City] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        for row_number, row in enumerate(csv.DictReader(stream), start=2):
            population = (row.get("population") or "").strip()
            if require_population and not population:
                continue
            city_name = _required(row, "city", row_number)
            # The legacy SimpleMaps snapshot has one populated row without an
            # ASCII spelling. Keeping the Unicode name is safer than dropping it.
            city_ascii = (row.get("city_ascii") or "").strip() or city_name
            country = _required(row, "country", row_number)
            if country == "Czechia":
                country = "Czech Republic"
            cities.append(
                City(
                    city=city_name,
                    city_ascii=city_ascii,
                    lat=float(_required(row, "lat", row_number)),
                    lng=float(_required(row, "lng", row_number)),
                    country=country,
                    iso2=_required(row, "iso2", row_number),
                    iso3=_required(row, "iso3", row_number),
                    admin_name=(row.get("admin_name") or "").strip(),
                    capital=(row.get("capital") or "").strip(),
                    population=int(float(population)) if population else None,
                    source_id=int(_required(row, "id", row_number)),
                )
            )
    return cities


def load_city_translations(path: str | Path) -> TranslationCatalog:
    cities: dict[tuple[str, str], str] = {}
    countries: dict[str, str] = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        for row_number, row in enumerate(csv.DictReader(stream), start=2):
            iso2 = _required(row, "iso2", row_number)
            city_ascii = _required(row, "city_ascii", row_number)
            city_ru = (row.get("city_ru") or "").strip()
            country_ru = (row.get("country_ru") or "").strip()
            if city_ru:
                cities[(iso2, city_ascii.casefold())] = city_ru
            if country_ru:
                countries[iso2] = country_ru
    return TranslationCatalog(cities=cities, countries=countries)


def merge_translation_catalogs(
    *catalogs: TranslationCatalog,
) -> TranslationCatalog:
    """Merge catalogs left-to-right, allowing profile-specific corrections."""

    cities: dict[tuple[str, str], str] = {}
    countries: dict[str, str] = {}
    for catalog in catalogs:
        cities.update(catalog.cities)
        countries.update(catalog.countries)
    return TranslationCatalog(cities=cities, countries=countries)


def apply_translations(
    cities: Iterable[City], catalog: TranslationCatalog | None
) -> list[City]:
    if catalog is None:
        return list(cities)
    return [catalog.apply(city) for city in cities]


def _serialize(city: City, column: str) -> str | int | float:
    if column == "ranking_reasons":
        return "|".join(city.ranking_reasons)
    value = getattr(city, column)
    return "" if value is None else value


def write_city_index(
    cities: Sequence[City],
    path: str | Path,
    *,
    profile: str,
) -> None:
    columns = DSML_COLUMNS if profile == "dsml" else HSPACE_COLUMNS
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for city in cities:
            writer.writerow({column: _serialize(city, column) for column in columns})


def _serialize_organization(
    organization: ResearchOrganization, column: str
) -> str | int | float:
    if column == "display_name":
        return organization.display_name
    if column == "search_names":
        return "|".join(organization.all_names)
    if column == "acronyms":
        return "|".join(organization.names_of_type("acronym"))
    if column == "aliases":
        return "|".join(organization.names_of_type("alias"))
    if column == "labels":
        return "|".join(organization.names_of_type("label"))
    if column in {"ranking_reasons", "types", "domains"}:
        return "|".join(getattr(organization, column))
    value = getattr(organization, column)
    return "" if value is None else value


def write_university_index(
    organizations: Sequence[ResearchOrganization], path: str | Path
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=UNIVERSITY_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        for organization in organizations:
            writer.writerow(
                {
                    column: _serialize_organization(organization, column)
                    for column in UNIVERSITY_COLUMNS
                }
            )


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_array(values: Iterable[str]) -> str:
    resolved = tuple(values)
    if not resolved:
        return "array[]::text[]"
    return "array[" + ",".join(_sql_text(value) for value in resolved) + "]::text[]"


def write_university_seed_sql(
    organizations: Sequence[ResearchOrganization],
    path: str | Path,
    *,
    source_release: str,
    batch_size: int = 500,
) -> None:
    """Write deterministic, batched inserts for public.university_index."""

    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    columns = (
        "ror_id",
        "priority",
        "ranking_score",
        "display_name",
        "normalized_name",
        "search_names",
        "acronyms",
        "aliases",
        "labels",
        "domains",
        "search_text",
        "country",
        "country_code",
        "city",
        "admin_name",
        "geonames_id",
        "lat",
        "lng",
        "established",
        "organization_types",
        "website",
        "source_release",
    )

    with destination.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(
            "-- Generated from the canonical ROR JSON dump. Do not edit manually.\n"
            f"-- Source release: {source_release}\n\n"
            "begin;\n\n"
            "delete from public.university_index;\n\n"
        )
        for offset in range(0, len(organizations), batch_size):
            batch = organizations[offset : offset + batch_size]
            stream.write(
                "insert into public.university_index (\n  "
                + ", ".join(columns)
                + "\n) values\n"
            )
            rows: list[str] = []
            for organization in batch:
                search_names = tuple(
                    dict.fromkeys(
                        normalize_search_text(name)
                        for name in organization.all_names
                        if normalize_search_text(name)
                    )
                )
                normalized_domains = university_search_domains(organization)
                search_text = " ".join(
                    dict.fromkeys((*search_names, *normalized_domains))
                )
                values = (
                    _sql_text(organization.ror_id),
                    str(organization.priority),
                    str(organization.ranking_score),
                    _sql_text(organization.display_name),
                    _sql_text(normalize_search_text(organization.display_name)),
                    _sql_array(search_names),
                    _sql_array(organization.names_of_type("acronym")),
                    _sql_array(organization.names_of_type("alias")),
                    _sql_array(organization.names_of_type("label")),
                    _sql_array(normalized_domains),
                    _sql_text(search_text),
                    _sql_text(organization.country),
                    _sql_text(organization.country_code),
                    _sql_text(organization.city),
                    _sql_text(organization.admin_name),
                    str(organization.geonames_id),
                    repr(organization.lat),
                    repr(organization.lng),
                    "null" if organization.established is None else str(organization.established),
                    _sql_array(organization.types),
                    _sql_text(organization.website),
                    _sql_text(source_release),
                )
                rows.append("  (" + ", ".join(values) + ")")
            stream.write(",\n".join(rows) + ";\n\n")
        stream.write("commit;\n")

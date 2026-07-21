from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import Iterable

from .models import City


EUROPEAN_COUNTRIES = frozenset(
    {
        "Albania", "Andorra", "Austria", "Belgium", "Bosnia and Herzegovina",
        "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia",
        "Finland", "France", "Germany", "Greece", "Vatican", "Hungary", "Iceland",
        "Ireland", "Italy", "Kosovo", "Latvia", "Liechtenstein", "Lithuania",
        "Luxembourg", "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands",
        "North Macedonia", "Norway", "Poland", "Portugal", "Romania", "San Marino",
        "Serbia", "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland",
        "United Kingdom",
    }
)

EXPAT_COUNTRY_LIMITS = {
    "Canada": 8, "United Arab Emirates": 5, "Israel": 3, "Saudi Arabia": 5,
    "Qatar": 2, "United States": 50, "Australia": 5, "Japan": 9,
    "Thailand": 5, "Philippines": 2, "Turkey": 5, "Mexico": 5,
    "Korea, South": 15, "Vietnam": 10, "Argentina": 2, "Taiwan": 1,
    "Malaysia": 1, "Hong Kong": 1,
}

CENTRAL_ASIA_COUNTRY_LIMITS = {
    "Kyrgyzstan": 3, "Uzbekistan": 16, "Armenia": 4, "Georgia": 4,
    "Azerbaijan": 4, "Turkmenistan": 3,
}

SLAVIC_COUNTRY_LIMITS = {"Russia": 20, "Ukraine": 10, "Belarus": 3}

LARGE_COUNTRY_LIMITS = {
    "China": 10, "India": 8, "Brazil": 5, "Pakistan": 2, "Iran": 2,
    "Indonesia": 3, "Egypt": 3, "Colombia": 2, "South Africa": 2,
}

GROUP_THRESHOLDS = {
    "kz_cities": 200_000,
    "european_cities": 1_000_000,
    "expat_cities": 1_500_000,
    "central_asia_cities": 350_000,
    "slavic_cities": 1_100_000,
    "large_countries_cities": 20_000_000,
}


def _first_by_country(cities: list[City], limits: dict[str, int]) -> list[City]:
    selected: list[City] = []
    counts: defaultdict[str, int] = defaultdict(int)
    for city in cities:
        limit = limits.get(city.country)
        if limit is not None and counts[city.country] < limit:
            selected.append(city)
            counts[city.country] += 1
    return selected


def _legacy_groups(cities: list[City]) -> dict[str, list[City]]:
    return {
        "kz_cities": [city for city in cities if city.country == "Kazakhstan"][:30],
        "european_cities": [
            city for city in cities if city.country in EUROPEAN_COUNTRIES
        ][:100],
        "expat_cities": _first_by_country(cities, EXPAT_COUNTRY_LIMITS),
        "central_asia_cities": _first_by_country(
            cities, CENTRAL_ASIA_COUNTRY_LIMITS
        ),
        "slavic_cities": _first_by_country(cities, SLAVIC_COUNTRY_LIMITS),
        "large_countries_cities": _first_by_country(cities, LARGE_COUNTRY_LIMITS),
    }


def _one_city_from_other_top_countries(
    cities: list[City], represented_countries: set[str]
) -> list[City]:
    candidates = [city for city in cities if city.country not in represented_countries]
    country_population: defaultdict[str, int] = defaultdict(int)
    first_city: dict[str, City] = {}
    for city in candidates:
        country_population[city.country] += city.population
        first_city.setdefault(city.country, city)

    top_countries = sorted(
        country_population,
        key=lambda country: country_population[country],
        reverse=True,
    )[:30]
    return sorted(
        (first_city[country] for country in top_countries),
        key=lambda city: city.population,
        reverse=True,
    )


def build_dsml_index(cities: Iterable[City]) -> list[City]:
    """Reproduce the selection and ordering encoded in the legacy notebook."""

    source = [city for city in cities if city.population is not None]
    groups = _legacy_groups(source)
    priority: list[City] = []
    non_priority: list[City] = []
    for group_name, group in groups.items():
        ordered = sorted(group, key=lambda city: city.population, reverse=True)
        threshold = GROUP_THRESHOLDS[group_name]
        priority.extend(city for city in ordered if city.population >= threshold)
        non_priority.extend(city for city in ordered if city.population < threshold)

    selected = priority + non_priority
    selected.extend(
        _one_city_from_other_top_countries(
            source, {city.country for city in selected}
        )
    )
    return [
        replace(
            city,
            population=(city.population // 1_000) * 1_000,
            priority=index,
            ranking_reasons=("legacy-dsml-order",),
        )
        for index, city in enumerate(selected)
    ]

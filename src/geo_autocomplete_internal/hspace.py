from __future__ import annotations

from dataclasses import dataclass
from math import log10
from typing import Iterable

from .dsml import EUROPEAN_COUNTRIES
from .models import City


MIDDLE_EAST_COUNTRIES = frozenset(
    {
        "Bahrain", "Egypt", "Iran", "Iraq", "Israel", "Jordan", "Kuwait",
        "Lebanon", "Oman", "Qatar", "Saudi Arabia", "Turkey",
        "United Arab Emirates",
    }
)

# These are deliberately product priors, not claimed measurements of researcher counts.
# Keep the values small enough that a major global city can outrank a tiny focus-market city.
COUNTRY_BONUSES = {
    "Singapore": 7.0,
    "China": 6.0,
    "United States": 6.0,
    "Hong Kong": 5.5,
    "India": 5.0,
    "Japan": 5.0,
    "Taiwan": 5.0,
    "Korea, South": 4.5,
    "Canada": 4.0,
    "Australia": 4.0,
}


@dataclass(frozen=True, slots=True)
class ResearchHub:
    iso2: str
    city_ascii: str
    admin_name: str | None = None
    bonus: float = 12.0

    def matches(self, city: City) -> bool:
        return (
            city.iso2 == self.iso2
            and city.city_ascii.casefold() == self.city_ascii.casefold()
            and (self.admin_name is None or city.admin_name == self.admin_name)
        )


RESEARCH_HUBS = (
    ResearchHub("US", "San Francisco", "California"),
    ResearchHub("US", "San Jose", "California"),
    ResearchHub("US", "Palo Alto", "California"),
    ResearchHub("US", "Berkeley", "California"),
    ResearchHub("US", "Stanford", "California"),
    ResearchHub("US", "Boston", "Massachusetts"),
    ResearchHub("US", "Cambridge", "Massachusetts"),
    ResearchHub("US", "New York", "New York"),
    ResearchHub("US", "Seattle", "Washington"),
    ResearchHub("US", "Pittsburgh", "Pennsylvania"),
    ResearchHub("US", "Princeton", "New Jersey"),
    ResearchHub("US", "Ithaca", "New York"),
    ResearchHub("US", "Ann Arbor", "Michigan"),
    ResearchHub("CA", "Toronto", "Ontario"),
    ResearchHub("CA", "Montreal", "Quebec"),
    ResearchHub("GB", "London", "London, City of"),
    ResearchHub("GB", "Cambridge", "Cambridgeshire"),
    ResearchHub("GB", "Oxford", "Oxfordshire"),
    ResearchHub("FR", "Paris"),
    ResearchHub("DE", "Berlin"),
    ResearchHub("DE", "Munich"),
    ResearchHub("DE", "Tubingen"),
    ResearchHub("CH", "Zurich"),
    ResearchHub("CH", "Lausanne"),
    ResearchHub("NL", "Amsterdam"),
    ResearchHub("NL", "Delft"),
    ResearchHub("CN", "Beijing"),
    ResearchHub("CN", "Shanghai"),
    ResearchHub("CN", "Shenzhen"),
    ResearchHub("CN", "Hangzhou"),
    ResearchHub("CN", "Nanjing"),
    ResearchHub("CN", "Guangzhou"),
    ResearchHub("CN", "Wuhan"),
    ResearchHub("CN", "Hefei"),
    ResearchHub("HK", "Hong Kong"),
    ResearchHub("TW", "Taipei"),
    ResearchHub("TW", "Hsinchu"),
    ResearchHub("SG", "Singapore", bonus=14.0),
    ResearchHub("IN", "Delhi"),
    ResearchHub("IN", "Bangalore"),
    ResearchHub("IN", "Mumbai"),
    ResearchHub("IN", "Hyderabad"),
    ResearchHub("IN", "Chennai"),
    ResearchHub("JP", "Tokyo"),
    ResearchHub("JP", "Kyoto"),
    ResearchHub("JP", "Osaka"),
    ResearchHub("KR", "Seoul"),
    ResearchHub("KR", "Daejeon"),
    ResearchHub("IL", "Tel Aviv-Yafo"),
    ResearchHub("IL", "Jerusalem"),
    ResearchHub("AE", "Abu Dhabi"),
    ResearchHub("AE", "Dubai"),
    ResearchHub("QA", "Doha"),
    ResearchHub("SA", "Riyadh"),
)


@dataclass(frozen=True, slots=True)
class HSpaceOptions:
    min_population: int = 50_000
    include_all: bool = False


def _hub_bonus(city: City) -> float:
    return max(
        (hub.bonus for hub in RESEARCH_HUBS if hub.matches(city)),
        default=0.0,
    )


def _country_bonus(city: City) -> float:
    configured = COUNTRY_BONUSES.get(city.country)
    if configured is not None:
        return configured
    if city.country in EUROPEAN_COUNTRIES:
        return 4.0
    if city.country in MIDDLE_EAST_COUNTRIES:
        return 4.0
    return 0.0


def _score(city: City) -> tuple[float, tuple[str, ...]]:
    score = 0.0
    reasons: list[str] = []
    if city.population is not None:
        score = 10.0 * log10(max(city.population, 1))
        reasons.append("population")

    country_bonus = _country_bonus(city)
    if country_bonus:
        score += country_bonus
        reasons.append("focus-region")

    hub_bonus = _hub_bonus(city)
    if hub_bonus:
        score += hub_bonus
        reasons.append("research-hub")

    if city.capital == "primary":
        score += 3.0
        reasons.append("national-capital")

    return round(score, 4), tuple(reasons)


def _included(city: City, options: HSpaceOptions) -> bool:
    return (
        options.include_all
        or (city.population is not None and city.population >= options.min_population)
        or city.capital == "primary"
        or _hub_bonus(city) > 0
    )


def build_hspace_index(
    cities: Iterable[City], options: HSpaceOptions | None = None
) -> list[City]:
    """Build a global, research-oriented index from the shared city source."""

    resolved = options or HSpaceOptions()
    scored = [
        (city, *_score(city))
        for city in cities
        if _included(city, resolved)
    ]
    scored.sort(
        key=lambda item: (
            -item[1],
            -(item[0].population or 0),
            item[0].country.casefold(),
            item[0].city_ascii.casefold(),
            item[0].source_id,
        )
    )
    return [
        city.ranked(priority=index, score=score, reasons=reasons)
        for index, (city, score, reasons) in enumerate(scored)
    ]

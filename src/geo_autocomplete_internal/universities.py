from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlparse

from .dsml import EUROPEAN_COUNTRIES
from .hspace import COUNTRY_BONUSES, MIDDLE_EAST_COUNTRIES, RESEARCH_HUBS
from .models import ResearchOrganization


_NON_WORD = re.compile(r"[^\w]+", flags=re.UNICODE)


def normalize_search_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(_NON_WORD.sub(" ", without_marks).split())


def _country_bonus(organization: ResearchOrganization) -> float:
    configured = COUNTRY_BONUSES.get(organization.country)
    if configured is not None:
        return configured
    if organization.country in EUROPEAN_COUNTRIES:
        return 4.0
    if organization.country in MIDDLE_EAST_COUNTRIES:
        return 4.0
    return 0.0


def _hub_bonus(organization: ResearchOrganization) -> float:
    return max(
        (
            hub.bonus
            for hub in RESEARCH_HUBS
            if hub.iso2 == organization.country_code
            and hub.city_ascii.casefold() == organization.city.casefold()
        ),
        default=0.0,
    )


def _score(organization: ResearchOrganization) -> tuple[float, tuple[str, ...]]:
    score = 0.0
    reasons: list[str] = []

    country_bonus = _country_bonus(organization)
    if country_bonus:
        score += country_bonus
        reasons.append("focus-region")

    hub_bonus = _hub_bonus(organization)
    if hub_bonus:
        score += hub_bonus
        reasons.append("research-hub")

    if organization.names_of_type("acronym"):
        score += 0.5
        reasons.append("acronym")
    if organization.names_of_type("alias"):
        score += 0.25
        reasons.append("alias")
    if any(name.language for name in organization.names):
        score += 0.25
        reasons.append("localized-name")
    if organization.website:
        score += 0.25
        reasons.append("website")
    if organization.domains:
        score += 0.25
        reasons.append("domain")
    if "funder" in organization.types:
        score += 2.0
        reasons.append("research-funder")

    return round(score, 4), tuple(reasons)


def build_university_index(
    organizations: Iterable[ResearchOrganization],
) -> list[ResearchOrganization]:
    """Rank active educational ROR organizations for the HSpace index."""

    scored = [
        (organization, *_score(organization))
        for organization in organizations
        if organization.status == "active" and "education" in organization.types
    ]
    scored.sort(
        key=lambda item: (
            -item[1],
            item[0].display_name.casefold(),
            item[0].country.casefold(),
            item[0].ror_id,
        )
    )
    return [
        organization.ranked(priority, score, reasons)
        for priority, (organization, score, reasons) in enumerate(scored)
    ]


def university_search_domains(
    organization: ResearchOrganization,
) -> tuple[str, ...]:
    """Return normalized ROR domains plus the canonical website hostname."""

    terms = list(organization.domains)
    if organization.website:
        hostname = urlparse(organization.website).hostname
        if hostname:
            terms.append(hostname.removeprefix("www."))
    return tuple(dict.fromkeys(normalize_search_text(term) for term in terms))


@dataclass(frozen=True, slots=True)
class _SearchEntry:
    organization: ResearchOrganization
    terms: tuple[str, ...]
    name_words: tuple[tuple[int, str], ...]


def _search_entry(organization: ResearchOrganization) -> _SearchEntry:
    names = tuple(normalize_search_text(name) for name in organization.all_names)
    return _SearchEntry(
        organization=organization,
        terms=names + university_search_domains(organization),
        name_words=tuple(
            (word_index, word)
            for name in names
            for word_index, word in enumerate(name.split())
        ),
    )


def _match_key(entry: _SearchEntry, query: str) -> tuple[int, int, int] | None:
    matches: list[tuple[int, int, int]] = []
    for term in entry.terms:
        if query == term:
            matches.append((0, 0, len(term)))
        elif term.startswith(query):
            matches.append((1, len(term) - len(query), len(term)))
        elif query in term:
            matches.append((3, term.index(query), len(term)))
    for word_index, word in entry.name_words:
        if word.startswith(query):
            matches.append((2, word_index, len(word) - len(query)))
    return min(matches) if matches else None


class UniversitySearchIndex:
    """Precomputed in-memory search terms for interactive autocomplete."""

    def __init__(self, organizations: Iterable[ResearchOrganization]) -> None:
        self._entries = tuple(_search_entry(item) for item in organizations)

    def search(self, query: str, *, limit: int = 10) -> list[ResearchOrganization]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        normalized_query = normalize_search_text(query)
        candidates: list[
            tuple[tuple[int, int, int], ResearchOrganization]
        ] = []
        for entry in self._entries:
            if not normalized_query:
                match_key = (0, 0, 0)
            else:
                match_key = _match_key(entry, normalized_query)
                if match_key is None:
                    continue
            candidates.append((match_key, entry.organization))

        candidates.sort(
            key=lambda item: (
                item[0][0],
                item[1].priority if item[1].priority is not None else 10**9,
                item[0][1],
                item[0][2],
                -(item[1].ranking_score or 0.0),
                item[1].display_name.casefold(),
                item[1].ror_id,
            )
        )
        return [organization for _, organization in candidates[:limit]]


def search_universities(
    organizations: Iterable[ResearchOrganization],
    query: str,
    *,
    limit: int = 10,
) -> list[ResearchOrganization]:
    """Run a one-off search; reuse UniversitySearchIndex for interactive use."""

    return UniversitySearchIndex(organizations).search(query, limit=limit)

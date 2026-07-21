from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlparse

from stateless_autocomplete import (
    AutocompleteIndex,
    SearchDocument,
    SearchTerm,
    normalize_text,
)

from .dsml import EUROPEAN_COUNTRIES
from .hspace import COUNTRY_BONUSES, MIDDLE_EAST_COUNTRIES, RESEARCH_HUBS
from .models import ResearchOrganization


def normalize_search_text(value: str) -> str:
    """Backward-compatible domain alias for the public normalizer."""

    return normalize_text(value)


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
    """Rank active educational ROR organizations for the shared index."""

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


def _search_document(
    organization: ResearchOrganization,
) -> SearchDocument[ResearchOrganization]:
    return SearchDocument(
        key=organization.ror_id,
        label=organization.display_name,
        payload=organization,
        terms=(
            *(
                SearchTerm(name, token_prefix=True)
                for name in organization.all_names
            ),
            *(
                SearchTerm(domain, token_prefix=False)
                for domain in university_search_domains(organization)
            ),
        ),
        priority=(
            organization.priority
            if organization.priority is not None
            else 10**9
        ),
        score=organization.ranking_score or 0.0,
    )


class UniversitySearchIndex:
    """Precomputed in-memory search terms for interactive autocomplete."""

    def __init__(self, organizations: Iterable[ResearchOrganization]) -> None:
        self._index = AutocompleteIndex(
            _search_document(item) for item in organizations
        )

    def search(self, query: str, *, limit: int = 10) -> list[ResearchOrganization]:
        return self._index.search(query, limit=limit)


def search_universities(
    organizations: Iterable[ResearchOrganization],
    query: str,
    *,
    limit: int = 10,
) -> list[ResearchOrganization]:
    """Run a one-off search; reuse UniversitySearchIndex for interactive use."""

    return UniversitySearchIndex(organizations).search(query, limit=limit)

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import IntEnum
from math import isfinite
from typing import Generic, TypeVar


T = TypeVar("T")
Normalizer = Callable[[str], str]
_NON_WORD = re.compile(r"[^\w]+", flags=re.UNICODE)


def normalize_text(value: str) -> str:
    """Normalize human-readable text for deterministic autocomplete matching."""

    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(_NON_WORD.sub(" ", without_marks).split())


class MatchTier(IntEnum):
    """Stable text-match tiers, ordered from strongest to weakest."""

    EXACT = 0
    PREFIX = 1
    TOKEN_PREFIX = 2
    SUBSTRING = 3


@dataclass(frozen=True, slots=True)
class SearchTerm:
    """One searchable spelling attached to an autocomplete document."""

    value: str
    token_prefix: bool = True

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("search term must not be empty")


@dataclass(frozen=True, slots=True)
class SearchDocument(Generic[T]):
    """A payload plus the stable metadata needed for deterministic ranking."""

    key: str
    label: str
    payload: T
    terms: tuple[SearchTerm, ...]
    priority: int = 10**9
    score: float = 0.0

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("document key must not be empty")
        if not self.label.strip():
            raise ValueError("document label must not be empty")
        if not self.terms:
            raise ValueError("document must contain at least one search term")
        if self.priority < 0:
            raise ValueError("document priority must be non-negative")
        if not isfinite(self.score):
            raise ValueError("document score must be finite")


@dataclass(frozen=True, slots=True)
class AutocompleteMatch(Generic[T]):
    """A ranked result with enough metadata to explain why it matched."""

    document: SearchDocument[T]
    tier: MatchTier
    normalized_query: str
    matched_term: str | None

    @property
    def payload(self) -> T:
        return self.document.payload


@dataclass(frozen=True, slots=True)
class _CompiledTerm:
    source: SearchTerm
    normalized: str
    words: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _CompiledDocument(Generic[T]):
    source: SearchDocument[T]
    terms: tuple[_CompiledTerm, ...]


def _compile_terms(
    terms: Iterable[SearchTerm],
    normalizer: Normalizer,
) -> tuple[_CompiledTerm, ...]:
    resolved: dict[str, SearchTerm] = {}
    for term in terms:
        normalized = normalizer(term.value)
        if not normalized:
            continue
        existing = resolved.get(normalized)
        if existing is None:
            resolved[normalized] = term
        elif term.token_prefix and not existing.token_prefix:
            resolved[normalized] = SearchTerm(
                value=existing.value,
                token_prefix=True,
            )
    return tuple(
        _CompiledTerm(
            source=term,
            normalized=normalized,
            words=tuple(normalized.split()) if term.token_prefix else (),
        )
        for normalized, term in resolved.items()
    )


def _term_match_key(
    term: _CompiledTerm,
    query: str,
) -> tuple[int, int, int] | None:
    matches: list[tuple[int, int, int]] = []
    if query == term.normalized:
        matches.append((MatchTier.EXACT, 0, len(term.normalized)))
    elif term.normalized.startswith(query):
        matches.append(
            (
                MatchTier.PREFIX,
                len(term.normalized) - len(query),
                len(term.normalized),
            )
        )
    elif query in term.normalized:
        matches.append(
            (
                MatchTier.SUBSTRING,
                term.normalized.index(query),
                len(term.normalized),
            )
        )
    for word_index, word in enumerate(term.words):
        if word.startswith(query):
            matches.append(
                (
                    MatchTier.TOKEN_PREFIX,
                    word_index,
                    len(word) - len(query),
                )
            )
    return min(matches) if matches else None


def _document_match(
    document: _CompiledDocument[T],
    query: str,
) -> tuple[tuple[int, int, int], str | None] | None:
    if not query:
        return (MatchTier.EXACT, 0, 0), None

    candidates: list[tuple[tuple[int, int, int], str]] = []
    for term in document.terms:
        key = _term_match_key(term, query)
        if key is not None:
            candidates.append((key, term.source.value))
    return min(candidates, key=lambda candidate: candidate[0]) if candidates else None


class AutocompleteIndex(Generic[T]):
    """Immutable in-memory autocomplete over caller-owned payloads.

    The index performs no network or storage access. Text-match quality always
    wins; static priority and score only order documents inside the same tier.
    """

    def __init__(
        self,
        documents: Iterable[SearchDocument[T]],
        *,
        normalizer: Normalizer = normalize_text,
    ) -> None:
        compiled: list[_CompiledDocument[T]] = []
        keys: set[str] = set()
        for document in documents:
            if document.key in keys:
                raise ValueError(f"duplicate document key: {document.key}")
            keys.add(document.key)
            terms = _compile_terms(document.terms, normalizer)
            if not terms:
                raise ValueError(
                    f"document {document.key!r} has no searchable terms"
                )
            compiled.append(_CompiledDocument(source=document, terms=terms))
        self._documents = tuple(compiled)
        self._normalizer = normalizer

    def __len__(self) -> int:
        return len(self._documents)

    def match(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[AutocompleteMatch[T]]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        if limit == 0:
            return []

        normalized_query = self._normalizer(query)
        candidates: list[
            tuple[tuple[int, int, int], str | None, _CompiledDocument[T]]
        ] = []
        for document in self._documents:
            matched = _document_match(document, normalized_query)
            if matched is None:
                continue
            match_key, matched_term = matched
            candidates.append((match_key, matched_term, document))

        candidates.sort(
            key=lambda candidate: (
                candidate[0][0],
                candidate[2].source.priority,
                candidate[0][1],
                candidate[0][2],
                -candidate[2].source.score,
                candidate[2].source.label.casefold(),
                candidate[2].source.key,
            )
        )
        return [
            AutocompleteMatch(
                document=document.source,
                tier=MatchTier(match_key[0]),
                normalized_query=normalized_query,
                matched_term=matched_term,
            )
            for match_key, matched_term, document in candidates[:limit]
        ]

    def search(self, query: str, *, limit: int = 10) -> list[T]:
        """Return only caller payloads for the common autocomplete path."""

        return [match.payload for match in self.match(query, limit=limit)]

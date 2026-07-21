"""Public, dependency-free building blocks for stateless autocomplete."""

from .core import (
    AutocompleteIndex,
    AutocompleteMatch,
    MatchTier,
    SearchDocument,
    SearchTerm,
    normalize_text,
)

__all__ = [
    "AutocompleteIndex",
    "AutocompleteMatch",
    "MatchTier",
    "SearchDocument",
    "SearchTerm",
    "normalize_text",
]

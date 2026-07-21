from __future__ import annotations

import unittest

from stateless_autocomplete import (
    AutocompleteIndex,
    MatchTier,
    SearchDocument,
    SearchTerm,
    normalize_text,
)


def document(
    key: str,
    label: str,
    *terms: SearchTerm,
    priority: int = 100,
    score: float = 0.0,
) -> SearchDocument[str]:
    return SearchDocument(
        key=key,
        label=label,
        payload=key,
        terms=terms,
        priority=priority,
        score=score,
    )


class StatelessAutocompleteTest(unittest.TestCase):
    def test_normalization_is_case_accent_and_punctuation_insensitive(self) -> None:
        self.assertEqual(normalize_text("  École—AI  "), "ecole ai")

    def test_match_quality_wins_before_static_priority(self) -> None:
        index = AutocompleteIndex(
            (
                document(
                    "prefix",
                    "Laboratory",
                    SearchTerm("Laboratory"),
                    priority=0,
                ),
                document(
                    "exact",
                    "Lab",
                    SearchTerm("Lab"),
                    priority=500,
                ),
            )
        )
        matches = index.match("lab")
        self.assertEqual([match.payload for match in matches], ["exact", "prefix"])
        self.assertEqual(matches[0].tier, MatchTier.EXACT)
        self.assertEqual(matches[1].tier, MatchTier.PREFIX)

    def test_prefix_token_prefix_and_substring_are_distinct_tiers(self) -> None:
        index = AutocompleteIndex(
            (
                document("prefix", "Laboratory", SearchTerm("Laboratory")),
                document("token", "Alpha Lab", SearchTerm("Alpha Lab")),
                document("substring", "Collaboration", SearchTerm("Collaboration")),
            )
        )
        matches = index.match("lab")
        self.assertEqual(
            [(match.payload, match.tier) for match in matches],
            [
                ("prefix", MatchTier.PREFIX),
                ("token", MatchTier.TOKEN_PREFIX),
                ("substring", MatchTier.SUBSTRING),
            ],
        )

    def test_token_prefix_can_be_disabled_for_structured_terms(self) -> None:
        index = AutocompleteIndex(
            (
                document(
                    "domain",
                    "Example",
                    SearchTerm("example university org", token_prefix=False),
                ),
            )
        )
        match = index.match("university")[0]
        self.assertEqual(match.tier, MatchTier.SUBSTRING)

    def test_priority_and_score_produce_stable_same_tier_order(self) -> None:
        index = AutocompleteIndex(
            (
                document("later", "Later", SearchTerm("alpha"), priority=2),
                document(
                    "lower-score",
                    "Lower score",
                    SearchTerm("alpha"),
                    priority=1,
                    score=1.0,
                ),
                document(
                    "higher-score",
                    "Higher score",
                    SearchTerm("alpha"),
                    priority=1,
                    score=2.0,
                ),
            )
        )
        self.assertEqual(
            index.search("alpha"),
            ["higher-score", "lower-score", "later"],
        )

    def test_empty_query_returns_the_static_order(self) -> None:
        index = AutocompleteIndex(
            (
                document("second", "Second", SearchTerm("second"), priority=2),
                document("first", "First", SearchTerm("first"), priority=1),
            )
        )
        self.assertEqual(index.search(""), ["first", "second"])

    def test_result_exposes_matched_term_without_replacing_the_payload(self) -> None:
        index = AutocompleteIndex(
            (
                document(
                    "nu",
                    "Nazarbayev University",
                    SearchTerm("Nazarbayev University"),
                    SearchTerm("NU"),
                ),
            )
        )
        match = index.match("NU")[0]
        self.assertEqual(match.payload, "nu")
        self.assertEqual(match.matched_term, "NU")
        self.assertEqual(match.normalized_query, "nu")

    def test_duplicate_keys_and_invalid_limits_fail_early(self) -> None:
        repeated = document("same", "Same", SearchTerm("same"))
        with self.assertRaisesRegex(ValueError, "duplicate document key"):
            AutocompleteIndex((repeated, repeated))
        index = AutocompleteIndex((repeated,))
        with self.assertRaisesRegex(ValueError, "limit must be non-negative"):
            index.search("same", limit=-1)


if __name__ == "__main__":
    unittest.main()

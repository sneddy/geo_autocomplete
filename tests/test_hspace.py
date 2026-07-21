from __future__ import annotations

import unittest
from pathlib import Path

from geo_autocomplete_internal.hspace import (
    HSpaceOptions,
    RESEARCH_HUBS,
    build_hspace_index,
)
from geo_autocomplete_internal.io import load_world_cities


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class HSpaceIndexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = load_world_cities(
            PROJECT_ROOT / "input" / "worldcities.csv",
            require_population=False,
        )
        cls.index = build_hspace_index(cls.source)

    def test_unfiltered_mode_keeps_every_source_row(self) -> None:
        unfiltered = build_hspace_index(
            self.source, HSpaceOptions(include_all=True)
        )
        self.assertEqual(len(unfiltered), 47_868)

    def test_default_filter_is_broad_but_bounded(self) -> None:
        self.assertGreater(len(self.index), 11_000)
        self.assertLess(len(self.index), 12_000)
        self.assertGreaterEqual(len({city.iso2 for city in self.index}), 235)
        selected_ids = {city.source_id for city in self.index}
        for city in self.source:
            if city.capital == "primary":
                self.assertIn(city.source_id, selected_ids)

    def test_every_configured_research_hub_matches_the_source(self) -> None:
        for hub in RESEARCH_HUBS:
            with self.subTest(hub=hub):
                self.assertTrue(any(hub.matches(city) for city in self.source))

    def test_research_centres_missing_from_legacy_index_are_present(self) -> None:
        actual = {
            (city.iso2, city.city_ascii, city.admin_name)
            for city in self.index
        }
        expected = {
            ("SG", "Singapore", ""),
            ("US", "Cambridge", "Massachusetts"),
            ("GB", "Cambridge", "Cambridgeshire"),
            ("GB", "Oxford", "Oxfordshire"),
            ("US", "Palo Alto", "California"),
            ("US", "Princeton", "New Jersey"),
            ("US", "Stanford", "California"),
        }
        self.assertTrue(expected.issubset(actual))

    def test_global_ranking_is_not_kazakhstan_first(self) -> None:
        priorities = {
            (city.city_ascii, city.country): city.priority for city in self.index
        }
        self.assertLess(priorities[("Singapore", "Singapore")], 20)
        self.assertGreater(priorities[("Almaty", "Kazakhstan")], 500)
        top_countries = {city.country for city in self.index[:30]}
        self.assertTrue(
            {
                "China",
                "United States",
                "Singapore",
                "India",
                "Japan",
                "United Arab Emirates",
            }.issubset(top_countries)
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import csv
import unittest
from pathlib import Path

from geo_autocomplete_internal.dsml import build_dsml_index
from geo_autocomplete_internal.io import apply_translations, load_city_translations, load_world_cities


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DsmlIndexRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = load_world_cities(PROJECT_ROOT / "input" / "worldcities.csv")
        cls.catalog = load_city_translations(
            PROJECT_ROOT / "input" / "dsml_translations_ru.csv"
        )

    def test_source_snapshot_has_expected_populated_rows(self) -> None:
        self.assertEqual(len(self.source), 47_656)

    def test_legacy_selection_matches_checked_in_dsml_artifact(self) -> None:
        actual = apply_translations(build_dsml_index(self.source), self.catalog)
        with (PROJECT_ROOT / "cities_index_with_ru.csv").open(
            newline="", encoding="utf-8-sig"
        ) as stream:
            expected = list(csv.DictReader(stream))

        self.assertEqual(len(actual), 398)
        self.assertEqual(len(expected), len(actual))
        for priority, (city, row) in enumerate(zip(actual, expected)):
            with self.subTest(priority=priority, city=city.city_ascii):
                self.assertEqual(city.priority, priority)
                self.assertEqual(city.city, row["city"])
                self.assertEqual(city.city_ascii, row["city_ascii"])
                self.assertEqual(city.country, row["country"])
                self.assertEqual(city.iso2, row["iso2"])
                self.assertEqual(city.population, int(row["population"]))
                self.assertEqual(city.city_ru, row["city_ru"])
                self.assertEqual(city.country_ru, row["country_ru"])


if __name__ == "__main__":
    unittest.main()

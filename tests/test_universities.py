from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from geo_autocomplete_internal.io import (
    write_university_index,
    write_university_seed_sql,
)
from geo_autocomplete_internal.ror import iter_json_array, load_ror_organizations
from geo_autocomplete_internal.universities import (
    UniversitySearchIndex,
    build_university_index,
    normalize_search_text,
    search_universities,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "ror_sample.json"
FULL_DUMP = (
    PROJECT_ROOT
    / "input"
    / "ror_data"
    / "v2.10-2026-07-20-ror-data.json"
)


class UniversityIndexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.organizations = load_ror_organizations(FIXTURE)
        cls.index = build_university_index(cls.organizations)

    def test_streaming_parser_handles_small_chunks(self) -> None:
        records = list(iter_json_array(FIXTURE, chunk_size=17))
        self.assertEqual(len(records), 6)

    def test_loader_keeps_only_active_education_records(self) -> None:
        self.assertEqual(len(self.organizations), 4)
        self.assertTrue(
            all(
                organization.status == "active"
                and "education" in organization.types
                for organization in self.organizations
            )
        )

    def test_expected_universities_and_localized_names_are_present(self) -> None:
        by_id = {organization.ror_id: organization for organization in self.index}
        mbzuai = by_id["https://ror.org/0258gkt32"]
        nazarbayev = by_id["https://ror.org/052bx8q98"]
        self.assertIn("MBZUAI", mbzuai.names_of_type("acronym"))
        self.assertIn("NU", nazarbayev.names_of_type("acronym"))
        self.assertIn("Назарбаев Университет", nazarbayev.all_names)

    def test_search_prefers_exact_acronyms_and_supports_domains(self) -> None:
        search = UniversitySearchIndex(self.index)
        self.assertEqual(
            search.search("MBZUAI")[0].ror_id,
            "https://ror.org/0258gkt32",
        )
        self.assertEqual(
            search.search("nu.edu.kz")[0].ror_id,
            "https://ror.org/052bx8q98",
        )
        self.assertEqual(
            search.search("Назарбаев")[0].ror_id,
            "https://ror.org/052bx8q98",
        )
        self.assertEqual(
            search_universities(self.index, "Nazarbayev")[0].ror_id,
            "https://ror.org/052bx8q98",
        )

    def test_normalization_handles_case_accents_and_punctuation(self) -> None:
        self.assertEqual(normalize_search_text("  École—AI  "), "ecole ai")

    def test_static_priority_uses_global_research_hubs(self) -> None:
        priorities = {
            organization.ror_id: organization.priority
            for organization in self.index
        }
        self.assertLess(
            priorities["https://ror.org/00f54p054"],
            priorities["https://ror.org/052bx8q98"],
        )
        self.assertLess(
            priorities["https://ror.org/0258gkt32"],
            priorities["https://ror.org/052bx8q98"],
        )

    def test_csv_contains_searchable_names_and_stable_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "universities.csv"
            write_university_index(self.index, output)
            with output.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
        by_id = {row["ror_id"]: row for row in rows}
        self.assertIn("MBZUAI", by_id["https://ror.org/0258gkt32"]["search_names"])
        self.assertEqual(
            by_id["https://ror.org/052bx8q98"]["country_code"], "KZ"
        )

    def test_sql_seed_is_batched_and_contains_normalized_search_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "universities.sql"
            write_university_seed_sql(
                self.index,
                output,
                source_release="ror-test",
                batch_size=2,
            )
            sql = output.read_text(encoding="utf-8")
        self.assertEqual(sql.count("insert into public.university_index"), 2)
        self.assertIn("'https://ror.org/0258gkt32'", sql)
        self.assertIn("array['mbzuai'", sql)
        self.assertIn("'nazarbayev university'", sql)
        self.assertIn("'nu edu kz'", sql)

    @unittest.skipUnless(FULL_DUMP.is_file(), "full ROR dump is not available")
    def test_full_v210_dump_has_expected_release_coverage(self) -> None:
        organizations = load_ror_organizations(FULL_DUMP)
        ids = {organization.ror_id for organization in organizations}
        self.assertEqual(len(organizations), 24_725)
        self.assertEqual(len(ids), 24_725)
        self.assertIn("https://ror.org/0258gkt32", ids)
        self.assertIn("https://ror.org/052bx8q98", ids)


if __name__ == "__main__":
    unittest.main()

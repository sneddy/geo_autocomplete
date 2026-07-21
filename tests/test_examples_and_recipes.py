from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ExamplesAndRecipesTest(unittest.TestCase):
    def test_custom_catalog_uses_the_installed_public_api(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "examples" / "custom_catalog.py"),
                "ICML",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload[0]["item_id"], "conf-icml")

    def test_university_recipe_has_one_private_table_and_bounded_rpc(self) -> None:
        sql = (
            PROJECT_ROOT / "recipes" / "supabase" / "university_index.sql"
        ).read_text(encoding="utf-8")
        self.assertEqual(sql.count("create table public.university_index"), 1)
        self.assertIn("create or replace function public.search_university_suggestions_v1", sql)
        self.assertIn("bounded_limit integer := least", sql)
        self.assertIn("alter table public.university_index force row level security", sql)
        self.assertIn("grant all on table public.university_index to service_role", sql)
        self.assertNotIn("grant select on table public.university_index to anon", sql)
        self.assertNotIn("grant select on table public.university_index to authenticated", sql)


if __name__ == "__main__":
    unittest.main()

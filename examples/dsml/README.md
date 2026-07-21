# DSML.kz compatibility profile

DSML.kz is the compatibility example. Its city build preserves the exact
selection and ordering of the original notebook, including all 398 rows and
legacy Russian labels.

From the repository root:

```bash
python3 scripts/build_dsml_index.py
```

The command writes `dist/dsml/cities_index_with_ru.csv`. The regression suite
compares every generated row with the historical release artifact:

```bash
PYTHONPATH=src python3 -m unittest tests.test_dsml -v
```

DSML also uses the shared ROR university profile. Download the pinned ROR dump
as described in `input/ror_data/README.md`, then build a DSML-owned copy of the
portable artifact and its database seed:

```bash
python3 scripts/build_university_index.py \
  --output dist/dsml/universities_index.csv
python3 scripts/build_university_seed_sql.py \
  --output /tmp/dsml_university_seed.sql
```

Apply `recipes/supabase/university_index.sql` before the generated seed. The
HTTP API should call only the bounded RPC and return a strict public response;
the browser should never read the table directly. Existing university values
remain valid free text.

Reference consumers:

- [DSML backend](https://github.com/sneddy/dsmlkz_backend)
- [DSML frontend](https://github.com/sneddy/dsmlkz_frontend)

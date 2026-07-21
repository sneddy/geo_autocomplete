# HSpace research profile

HSpace is the broad-coverage example. Its city profile includes every city
above the configured population threshold, every national capital, and
explicit research hubs. Its university profile includes every active ROR
organization with the `education` type.

From the repository root:

```bash
python3 scripts/build_hspace_index.py
python3 scripts/build_university_index.py
```

This produces:

```text
dist/hspace/cities_index.csv
dist/hspace/universities_index.csv
```

The city threshold is an explicit profile choice, not framework behavior:

```bash
python3 scripts/build_hspace_index.py --min-population 100000
python3 scripts/build_hspace_index.py --all
```

For the production-style database path, apply the typed schema and generate a
deterministic seed:

```bash
psql "$DATABASE_URL" -f recipes/supabase/university_index.sql
python3 scripts/build_university_seed_sql.py \
  --output /tmp/hspace_university_seed.sql
psql "$DATABASE_URL" -f /tmp/hspace_university_seed.sql
```

The reference UI uses a two-character debounce, a bounded public API route,
and a free-text fallback. Selecting a suggestion stores only its display name;
it does not verify institutional membership.

Reference consumer: [HSpace](https://github.com/sneddy/hspace).

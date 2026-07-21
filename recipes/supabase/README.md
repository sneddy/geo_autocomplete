# Supabase/PostgreSQL reference adapter

`university_index.sql` is the typed database adapter used by both reference
sites. It creates one private table, normalization and bounded-search RPCs, and
the indexes needed by the generated ROR seed.

The adapter is deliberately not a universal schema generator:

- the public Python core works with any caller-owned payload;
- this SQL file is specific to the included ROR university artifact;
- HTTP contracts, authentication, caching, and migrations remain application
  concerns.

This boundary adds a reproducible production path without turning the project
into an ORM or deployment framework.

## Apply

Create the foundation first, then generate and apply the seed:

```bash
psql "$DATABASE_URL" -f recipes/supabase/university_index.sql
python3 scripts/build_university_seed_sql.py \
  --output /tmp/university_index_seed.sql
psql "$DATABASE_URL" -f /tmp/university_index_seed.sql
```

For Supabase CLI projects, copy the foundation and generated seed into two
ordered migration files instead. Review `supabase migration list --linked`
before pushing so unrelated pending migrations are not applied accidentally.

## Security model

Direct reads are denied to `anon` and `authenticated`. Those roles can execute
only the bounded `search_university_suggestions_v1` RPC. The `service_role`
owns seed and maintenance access. A public HTTP service can call the RPC and
enforce its own response contract without exposing the table.

The role names and RLS statements are Supabase-specific. Plain PostgreSQL users
should replace them with equivalent application roles rather than weakening
the table permissions.

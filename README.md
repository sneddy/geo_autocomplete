# Stateless Autocomplete

[![Tests](https://github.com/sneddy/geo_autocomplete/actions/workflows/test.yml/badge.svg)](https://github.com/sneddy/geo_autocomplete/actions/workflows/test.yml)

Build deterministic autocomplete indexes from versioned data and search them
without a provider call, model request, or hidden ranking service.

The public `stateless_autocomplete` package works with any caller-owned record.
This repository also includes reproducible city and ROR university adapters
used by DSML.kz and HSpace.

## Product scenarios

Use this project when you need to:

- add autocomplete for universities, cities, labs, conferences, companies, or
  another controlled catalog;
- replace a request-time third-party search API with a versioned local index;
- give several products the same source data while keeping product-specific
  filtering and ranking explicit;
- serve a small index in memory or load a larger one into your own database;
- offer canonical suggestions without forcing users to abandon free-text input;
- explain why one result ranked above another and reproduce that order later.

The library owns text normalization, match tiers, and deterministic ordering.
Your application still owns data policy, transport, caching, authentication,
analytics, and the combobox UI.

## Quick start

Python 3.10 or newer is required.

```bash
python3 -m pip install --editable .
python3 examples/custom_catalog.py ICML
```

```python
from stateless_autocomplete import (
    AutocompleteIndex,
    SearchDocument,
    SearchTerm,
)

records = (
    SearchDocument(
        key="conf-icml",
        label="International Conference on Machine Learning",
        payload={"id": "conf-icml", "name": "ICML"},
        terms=(
            SearchTerm("International Conference on Machine Learning"),
            SearchTerm("ICML"),
        ),
        priority=0,
    ),
    SearchDocument(
        key="lab-mila",
        label="Mila - Quebec AI Institute",
        payload={"id": "lab-mila", "name": "Mila"},
        terms=(SearchTerm("Mila - Quebec AI Institute"), SearchTerm("Mila")),
        priority=1,
    ),
)

index = AutocompleteIndex(records)
suggestions = index.search("ICML", limit=10)
```

Use `index.match(...)` instead when you also need the winning match tier and
matched spelling for diagnostics or explanations.

## Matching model

The default normalizer handles case, accents, whitespace, and punctuation.
Candidates are ordered by:

1. exact term;
2. full-term prefix;
3. token prefix;
4. substring.

Text quality wins before caller-provided static priority and score. Final ties
use stable label and key ordering. There is intentionally no hidden typo model,
embedding service, popularity tracking, or personalization.

## Included adapters

| Adapter | Artifact | Coverage |
| --- | --- | ---: |
| DSML city compatibility profile | `dist/dsml/cities_index_with_ru.csv` | 398 |
| HSpace global city profile | `dist/hspace/cities_index.csv` | 11,364 |
| Active ROR education organizations | `dist/hspace/universities_index.csv` | 24,725 |

Rebuild them with:

```bash
python3 scripts/build_dsml_index.py
python3 scripts/build_hspace_index.py
python3 scripts/build_university_index.py
```

The pinned ROR dump must first be downloaded as described in
[`input/ror_data/README.md`](input/ror_data/README.md). All builders accept
explicit input and output paths.

Consumer-specific policy stays outside the generic engine. See the compact
recipes for [DSML](examples/dsml/) and [HSpace](examples/hspace/) rather than
the main README for their implementation details.

## Deployment choices

For a small or medium catalog, build `AutocompleteIndex` once at process start
and query it in memory. A 24,725-record ROR index builds in well under a second
on a typical development machine and has no request-time I/O.

For database-backed applications, the repository includes a scoped
[Supabase/PostgreSQL university recipe](recipes/supabase/). It creates one
private typed table, search indexes, normalization, a bounded RPC, and
restrictive RLS. Generate its deterministic seed with:

```bash
python3 scripts/build_university_seed_sql.py \
  --output /tmp/university_index_seed.sql
```

This is a production adapter for the included ROR dataset, not a universal ORM
or migration framework. HTTP contracts and deployment ordering remain the
consumer's responsibility.

## Reference consumers

- [DSML backend](https://github.com/sneddy/dsmlkz_backend) and
  [frontend](https://github.com/sneddy/dsmlkz_frontend)
- [HSpace](https://github.com/sneddy/hspace)

Both keep suggestions optional. Selecting a university or city does not prove
residence, employment, enrollment, or institutional membership.

## Project layout

```text
src/stateless_autocomplete/      public generic engine
src/geo_autocomplete_internal/  city and ROR adapters
scripts/                         reproducible builders
examples/                        custom, DSML, and HSpace consumers
recipes/supabase/                optional database adapter
dist/                            generated release artifacts
```

## Validation

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The suite covers the generic ranking contract, adapter reproducibility, ROR
search, SQL generation, and database permissions.

## Data and license

City data is based on the SimpleMaps World Cities Database under CC BY 4.0.
University data comes from ROR v2.10 under CC0, with GeoNames-derived location
fields under CC BY 4.0. See [`NOTICE.md`](NOTICE.md) for attribution.

Project code is released under the [MIT License](LICENSE).

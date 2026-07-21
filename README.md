# Stateless Autocomplete

[![Tests](https://github.com/sneddy/geo_autocomplete/actions/workflows/test.yml/badge.svg)](https://github.com/sneddy/geo_autocomplete/actions/workflows/test.yml)

Build deterministic autocomplete indexes from versioned datasets, then search
them without a provider call, model request, or hidden ranking service.

The repository has two layers:

- `stateless_autocomplete` is a public, dependency-free Python core for any
  caller-owned records;
- the city and ROR pipelines are reproducible domain adapters used by DSML.kz
  and HSpace.

The core owns normalization, match tiers, stable tie-breaking, and explainable
result metadata. Applications keep control of data selection, static priors,
storage, HTTP transport, caching, authentication, and UI state.

## Why this repository is useful

Autocomplete often starts as an ad hoc array filter and later becomes an
opaque hosted dependency. This project provides a small middle path:

```text
versioned source data
        ↓
deterministic profile and static priority
        ↓
portable CSV or SQL seed
        ↓
pure in-memory search or a bounded database RPC
        ↓
application-owned API and combobox
```

`stateless` means the query algorithm performs no network or storage access.
It searches an immutable set of documents supplied by the caller. The included
PostgreSQL recipe moves that same deterministic index into application-owned
storage; it does not turn this package into a hosted service.

## Quick start

Python 3.10 or newer is required.

```bash
python3 -m pip install --editable .
python3 examples/custom_catalog.py ICML
```

Use the public API with any payload type:

```python
from dataclasses import dataclass

from stateless_autocomplete import (
    AutocompleteIndex,
    SearchDocument,
    SearchTerm,
)


@dataclass(frozen=True)
class Item:
    item_id: str
    name: str
    aliases: tuple[str, ...]
    priority: int


items = (
    Item("conf-icml", "International Conference on Machine Learning", ("ICML",), 0),
    Item("lab-mila", "Mila - Quebec AI Institute", ("Mila",), 1),
)

index = AutocompleteIndex(
    SearchDocument(
        key=item.item_id,
        label=item.name,
        payload=item,
        terms=tuple(SearchTerm(value) for value in (item.name, *item.aliases)),
        priority=item.priority,
    )
    for item in items
)

suggestions = index.search("ICML", limit=10)
```

Call `index.match(...)` when the application also needs the winning match tier
and matched spelling for diagnostics or an explanation UI.

## Ranking contract

The public engine normalizes case, accents, whitespace, and punctuation, then
orders candidates by four explicit text tiers:

1. exact term;
2. full-term prefix;
3. token prefix;
4. substring.

Text quality always wins. Caller-provided priority and score only break ties
within the same text tier, followed by stable label and key ordering. Token
prefixes can be disabled for structured values such as domains.

There is deliberately no typo model, embedding service, popularity tracking,
or implicit personalization. Those can be application signals, but they should
not be hidden inside a supposedly reusable index.

## Included reproducible profiles

| Profile | Output | Current coverage | Purpose |
| --- | --- | ---: | --- |
| DSML cities | `dist/dsml/cities_index_with_ru.csv` | 398 | Exact legacy compatibility |
| HSpace cities | `dist/hspace/cities_index.csv` | 11,364 | Broad global research coverage |
| ROR universities | `dist/hspace/universities_index.csv` | 24,725 | Active educational organizations |

Download the pinned ROR release as described in
[`input/ror_data/README.md`](input/ror_data/README.md) before rebuilding the
university artifact.

```bash
python3 scripts/build_dsml_index.py
python3 scripts/build_hspace_index.py
python3 scripts/build_university_index.py
```

All commands accept explicit input and output paths. Run them with `--help` for
the complete interface.

### DSML compatibility profile

The DSML builder reproduces the original notebook behavior:

1. select fixed numbers of cities from the legacy country groups;
2. split groups around their configured population thresholds;
3. add one major city from 30 otherwise unrepresented countries;
4. round populations down to the nearest thousand;
5. preserve Russian labels and final priority order.

The regression suite compares every generated row with the historical artifact.
See [`examples/dsml/`](examples/dsml/) for the complete consumer recipe.

### HSpace research profile

The default HSpace city profile includes every city with at least 50,000
residents, every national capital, and configured AI/research hubs regardless
of population.

```bash
python3 scripts/build_hspace_index.py --min-population 100000
python3 scripts/build_hspace_index.py --all
```

Static city priority combines logarithmic population, a small focus-market
prior, research-hub bonuses, and a national-capital bonus. These are explicit
product priors, not claims about measured researcher counts. The weights live
in `src/geo_autocomplete_internal/hspace.py` and should be recalibrated against
real usage data when available.

The ROR adapter selects records with `status=active` and the `education` type.
It retains stable IDs, acronyms, aliases, multilingual labels, domains,
location, website, and source release. ROR's education type is intentionally
broad; clients should keep free-text affiliation input for missing or
non-institutional values.

See [`examples/hspace/`](examples/hspace/) for the complete consumer recipe.

## Database recipe

Publishing a table foundation adds value when it is a tested adapter for a
real artifact. Publishing a universal migration/ORM layer would blur the
project boundary, so this repository includes only the typed university recipe
used by both reference sites:

```text
recipes/supabase/university_index.sql
```

It creates one private `university_index` table, search indexes, normalization,
a bounded RPC, and restrictive RLS. Generate its deterministic batched seed:

```bash
python3 scripts/build_university_seed_sql.py \
  --output /tmp/university_index_seed.sql
```

Apply the foundation before the seed. Direct anonymous/authenticated table
reads remain denied; applications expose a strict HTTP contract over the RPC.
See [`recipes/supabase/`](recipes/supabase/) for deployment and security notes.

## Reference consumers

- [DSML backend](https://github.com/sneddy/dsmlkz_backend) and
  [frontend](https://github.com/sneddy/dsmlkz_frontend) use the compatibility
  city profile and their own copy of the ROR university index.
- [HSpace](https://github.com/sneddy/hspace) uses the global city profile and
  an independently seeded copy of the same ROR university index.

Both sites keep autocomplete optional and free text. A suggestion is canonical
metadata, not proof of residence, employment, enrollment, or institutional
membership.

## Architecture

```text
src/stateless_autocomplete/
  core.py                         public generic matching and ranking

src/geo_autocomplete_internal/
  models.py                       typed city and organization records
  dsml.py                         legacy compatibility profile
  hspace.py                       global research profile
  ror.py                          streaming ROR parser
  universities.py                ROR adapter over the public core
  io.py                           CSV and SQL seed exporters
  cli.py                          reusable build orchestration

scripts/                          stable build entrypoints
examples/                         custom, DSML, and HSpace consumers
recipes/supabase/                 optional typed database adapter
dist/                             reproducible release artifacts
```

The site-named modules contain profile policy, not framework behavior. The
scripts contain only argument handling. Reusable search behavior lives in the
public package and can be installed independently of the example builders.

## Validation

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/build_dsml_index.py --output /tmp/dsml.csv
python3 scripts/build_hspace_index.py --output /tmp/hspace.csv
python3 scripts/build_university_index.py \
  --source tests/fixtures/ror_sample.json \
  --output /tmp/universities.csv
python3 scripts/build_university_seed_sql.py \
  --source tests/fixtures/ror_sample.json \
  --source-release ror-test \
  --output /tmp/universities.sql
```

The suite covers the generic match contract, all 398 DSML compatibility rows,
HSpace coverage and research hubs, ROR streaming/filtering, acronym/domain/
localized-name matching, SQL seed generation, database recipe permissions, and
the presence of Nazarbayev University and MBZUAI in the pinned full release.

## Data provenance

The world-cities snapshot and derived city artifacts are based on the
[SimpleMaps World Cities Database](https://simplemaps.com/data/world-cities),
licensed under CC BY 4.0.

The university artifact is derived from ROR v2.10. ROR metadata is dedicated
to the public domain under CC0; its GeoNames-derived location fields are
licensed under CC BY 4.0. See [`NOTICE.md`](NOTICE.md) for full attribution.

The raw ROR JSON is not committed because it exceeds GitHub's file-size limit.

## Legacy notebook

`demo.ipynb` is retained as historical context for the DSML rules. It depends
on manual cell ordering and translation experiments and is not a production
build path.

## License

Project code is released under the [MIT License](LICENSE). Bundled source data
and derived datasets retain their respective licenses as described in
[`NOTICE.md`](NOTICE.md).

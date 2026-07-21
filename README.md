# Geo Autocomplete Index

[![Tests](https://github.com/sneddy/geo_autocomplete/actions/workflows/test.yml/badge.svg)](https://github.com/sneddy/geo_autocomplete/actions/workflows/test.yml)

Reproducible city and university indexes for the DSML and HSpace autocomplete
experiences. The city profiles share a versioned world-cities snapshot, while
the university profile uses the open Research Organization Registry (ROR):

- **DSML** preserves the exact 398-city legacy selection and ordering.
- **HSpace** provides broad global coverage with a research-oriented ranking.
- **HSpace Universities** provides stable IDs and multilingual search names for
  active educational research organizations.

The production pipelines are deterministic, offline, and dependency-free. The
legacy notebook remains available for historical context, but it is not part of
the canonical build path.

## Quick start

Python 3.10 or newer is required.

Download the pinned ROR release as described in `input/ror_data/README.md`
before building the university index.

```bash
python3 scripts/build_dsml_index.py
python3 scripts/build_hspace_index.py
python3 scripts/build_university_index.py
```

The generated files are written to:

```text
dist/dsml/cities_index_with_ru.csv
dist/hspace/cities_index.csv
dist/hspace/universities_index.csv
```

Use `--source`, `--translations`, and `--output` to override the default paths.
Run each command with `--help` for the complete interface.

To load the same university data into PostgreSQL, generate a deterministic SQL
seed after creating the `public.university_index` table:

```bash
python3 scripts/build_university_seed_sql.py \
  --output /path/to/migrations/university_index_ror_v210_seed.sql
```

The generated seed uses batches of 500 rows, records the source release on
every row, and can be reproduced independently by DSML and HSpace.

## Profiles

### DSML compatibility profile

The DSML builder reproduces the behavior encoded in the original notebook:

1. Select fixed numbers of cities from the legacy country groups.
2. Split each group around its configured population threshold.
3. Append one major city from 30 otherwise unrepresented countries.
4. Round population values down to the nearest thousand.
5. Preserve the legacy Russian labels and final priority order.

The checked-in regression test compares all 398 generated records with the
existing `cities_index_with_ru.csv` artifact.

Russian labels are stored in `input/dsml_translations_ru.csv`; the production
build never calls an online translation service. Legacy translations remain
unchanged so that the DSML output is stable. HSpace applies the small correction
catalog in `input/hspace_translation_overrides_ru.csv` on top of that data.

### HSpace research profile

The default HSpace profile includes:

- every city with at least 50,000 residents;
- every national capital;
- configured AI and research hubs regardless of population.

With the current source snapshot, this produces 11,364 records across 240
countries and territories. The output retains the administrative region so
clients can distinguish names such as Cambridge or Princeton.

Change the population threshold when building:

```bash
python3 scripts/build_hspace_index.py --min-population 100000
```

Export all 47,868 source records, including records without population data:

```bash
python3 scripts/build_hspace_index.py --all
```

The HSpace score combines:

- logarithmic population;
- a small focus-market prior;
- a research-hub bonus;
- a national-capital bonus.

The output exposes both `ranking_score` and `ranking_reasons`. Current focus
markets include the United States, Europe, Singapore, China, India, Japan,
South Korea, Canada, Australia, and the Middle East. These weights are explicit
product priors, not claims about measured researcher counts. They should be
recalibrated against OpenAlex, ROR, and HSpace usage data as the product grows.

Market weights and research hubs are configured in
`src/geo_autocomplete_internal/hspace.py`.

### HSpace university profile

The university builder uses only the canonical ROR JSON dump. Release v2.10
contains 132,537 research organizations; the profile selects the 24,725 records
that have `status=active` and include the `education` type. Each row retains:

- the stable ROR ID and display name;
- acronyms, aliases, and multilingual labels;
- country, city, administrative region, coordinates, and GeoNames ID;
- organization types, establishment year, domains, and official website;
- an explicit HSpace priority score and its component reasons.

ROR's `education` type is deliberately broad: it includes universities,
colleges, specialist institutes, and some secondary-education organizations.
The profile keeps this breadth to avoid silently removing valid affiliations.
Clients should keep a free-text fallback for organizations that are not yet in
ROR.

Autocomplete matching is implemented by `search_universities` in
`src/geo_autocomplete_internal/universities.py`. It applies exact, full-prefix,
token-prefix, and substring matching in that order across every ROR name and
the official domain. Static priority is only a tie-breaker within the same text
match quality; an empty-query global ranking is not intended as a university
league table.

```python
from geo_autocomplete_internal import (
    UniversitySearchIndex,
    build_university_index,
    load_ror_organizations,
)

universities = build_university_index(
    load_ror_organizations("input/ror_data/v2.10-2026-07-20-ror-data.json")
)
search = UniversitySearchIndex(universities)
suggestions = search.search("MBZUAI", limit=10)
```

The static score uses only ROR fields plus the existing transparent HSpace
focus-region and research-hub configuration. The `funder` type acts as a small
research-activity signal. No commercial rankings or external institution
datasets are incorporated.

The raw ROR JSON is not committed because it exceeds GitHub's file-size limit.
See `input/ror_data/README.md` for the pinned release and download instructions.

## Architecture

```text
input/worldcities.csv          input/ror_data/*.json
          \                              /
           +------------+---------------+
                        v
src/geo_autocomplete_internal/
        |-- dsml.py       legacy selection and ordering
        |-- hspace.py     global selection and research ranking
        |-- ror.py        streaming ROR JSON parsing
        |-- universities.py  organization ranking and query matching
        |-- io.py         parsing, translations, and CSV export
        |-- models.py     shared immutable city and organization models
        `-- cli.py        reusable build orchestration
        |
        +--> dist/dsml/cities_index_with_ru.csv
        +--> dist/hspace/cities_index.csv
        `--> dist/hspace/universities_index.csv
```

The scripts contain only command-line argument handling. Reusable behavior
lives in the internal package and can be imported by tests or future exporters.

## Validation

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The test suite verifies:

- exact DSML compatibility across all 398 records;
- full-source HSpace export behavior;
- default HSpace coverage and capital inclusion;
- configured research-hub resolution;
- representative global ranking behavior;
- streaming ROR parsing and active-education filtering;
- exact, prefix, localized-name, acronym, and domain matching;
- presence of Nazarbayev University and MBZUAI in the pinned full dump.

## Data provenance

The world-cities snapshot and derived CSV artifacts are based on the
[SimpleMaps World Cities Database](https://simplemaps.com/data/world-cities),
licensed under CC BY 4.0. See [NOTICE.md](NOTICE.md) for attribution details.

The university artifact is derived from ROR v2.10. ROR metadata is dedicated
to the public domain under CC0; its GeoNames-derived location fields are
licensed under CC BY 4.0. See [NOTICE.md](NOTICE.md) for details.

## Legacy notebook

`demo.ipynb` is retained as the historical source of the DSML rules. It relies
on manual cell ordering and translation experiments, so it should not be used
for production builds.

## License

Project code is released under the [MIT License](LICENSE). The bundled source
data and derived datasets retain their respective data licenses as described in
[NOTICE.md](NOTICE.md).

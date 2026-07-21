# Geo Autocomplete Index

[![Tests](https://github.com/sneddy/geo_autocomplete/actions/workflows/test.yml/badge.svg)](https://github.com/sneddy/geo_autocomplete/actions/workflows/test.yml)

Reproducible city indexes for the DSML and HSpace autocomplete experiences.
Both profiles are built from the same versioned world-cities snapshot, but they
serve different ranking goals:

- **DSML** preserves the exact 398-city legacy selection and ordering.
- **HSpace** provides broad global coverage with a research-oriented ranking.

The production pipelines are deterministic, offline, and dependency-free. The
legacy notebook remains available for historical context, but it is not part of
the canonical build path.

## Quick start

Python 3.10 or newer is required.

```bash
python3 scripts/build_dsml_index.py
python3 scripts/build_hspace_index.py
```

The generated files are written to:

```text
dist/dsml/cities_index_with_ru.csv
dist/hspace/cities_index.csv
```

Use `--source`, `--translations`, and `--output` to override the default paths.
Run either command with `--help` for the complete interface.

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

## Architecture

```text
input/worldcities.csv
        |
        v
src/geo_autocomplete_internal/
        |-- dsml.py       legacy selection and ordering
        |-- hspace.py     global selection and research ranking
        |-- io.py         parsing, translations, and CSV export
        |-- models.py     shared immutable data models
        `-- cli.py        reusable build orchestration
        |
        +--> dist/dsml/cities_index_with_ru.csv
        `--> dist/hspace/cities_index.csv
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
- representative global ranking behavior.

## Data provenance

The world-cities snapshot and derived CSV artifacts are based on the
[SimpleMaps World Cities Database](https://simplemaps.com/data/world-cities),
licensed under CC BY 4.0. See [NOTICE.md](NOTICE.md) for attribution details.

## Legacy notebook

`demo.ipynb` is retained as the historical source of the DSML rules. It relies
on manual cell ordering and translation experiments, so it should not be used
for production builds.

## License

Project code is released under the [MIT License](LICENSE). The bundled source
data and derived datasets retain their respective data licenses as described in
[NOTICE.md](NOTICE.md).

# Changelog

All notable changes to this project are documented in this file.

## [2.0.0] - 2026-07-21

### Added

- A public, dependency-free `stateless_autocomplete` package for arbitrary
  caller-owned records.
- Explicit exact, prefix, token-prefix, and substring match tiers with stable
  priority and score tie-breaking.
- Match metadata for diagnostics and explanation UIs.
- Reproducible custom-catalog, DSML, and HSpace consumer examples.
- A production-tested Supabase/PostgreSQL `university_index` foundation with a
  bounded RPC and restrictive table permissions.
- Regression coverage for the generic engine, executable example, and SQL
  deployment recipe.

### Changed

- Repositioned the repository as a stateless autocomplete toolkit with city
  and ROR pipelines as domain adapters rather than the whole product surface.
- Refactored university search to use the public generic engine without
  changing the released ROR index or ranking contract.
- Renamed the Python distribution from `geo-autocomplete-index` to
  `stateless-autocomplete`; the internal profile package remains available to
  the existing build scripts.

## [1.1.0] - 2026-07-21

### Added

- A ROR-only HSpace university autocomplete profile with 24,725 active
  educational organizations from release v2.10.
- Dependency-free streaming of the canonical ROR JSON dump.
- Stable ROR IDs, multilingual names, acronyms, domains, websites, and GeoNames
  locations in the generated university artifact.
- Reusable university query matching with exact, prefix, token-prefix, and
  substring tiers.
- Deterministic batched PostgreSQL seed generation for the shared
  `public.university_index` table.
- Regression coverage for Nazarbayev University, MBZUAI, source filtering, and
  the complete pinned ROR release.

### Changed

- Expanded the package scope from city-only indexes to geographic and
  affiliation autocomplete data.

## [1.0.0] - 2026-07-21

### Added

- A deterministic DSML compatibility pipeline that reproduces all 398 legacy
  city records and priorities.
- A global HSpace profile with configurable population filtering, national
  capitals, research hubs, focus-market priors, and a fully unfiltered mode.
- A dependency-free internal Python package for shared models, parsing,
  translations, ranking, and export behavior.
- Versioned Russian translation inputs and HSpace-specific corrections.
- Generated DSML and HSpace release artifacts.
- Regression and coverage tests across both profiles.
- GitHub Actions validation for supported Python versions.

### Changed

- Replaced the notebook-driven production workflow with explicit CLI scripts.
- Retained `demo.ipynb` as historical documentation only.

[1.0.0]: https://github.com/sneddy/geo_autocomplete/releases/tag/v1.0.0
[1.1.0]: https://github.com/sneddy/geo_autocomplete/compare/v1.0.0...v1.1.0
[2.0.0]: https://github.com/sneddy/geo_autocomplete/compare/v1.1.0...v2.0.0

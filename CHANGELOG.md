# Changelog

All notable changes to this project are documented in this file.

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

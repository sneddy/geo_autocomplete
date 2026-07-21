# Changelog

## [2.0.0] - 2026-07-21

- Added the public, dependency-free `stateless_autocomplete` engine for
  arbitrary caller-owned records.
- Formalized exact, prefix, token-prefix, and substring ranking with stable
  tie-breaking and match metadata.
- Added compact custom, DSML, and HSpace examples plus a production-tested
  Supabase university recipe.
- Kept existing city and ROR release artifacts byte-identical.

## [1.1.0] - 2026-07-21

- Added the 24,725-record ROR v2.10 university adapter, portable CSV artifact,
  in-memory search, and deterministic PostgreSQL seed generation.

## [1.0.0] - 2026-07-21

- Replaced the legacy notebook build with deterministic DSML and HSpace city
  profiles, versioned artifacts, and regression tests.

[1.0.0]: https://github.com/sneddy/geo_autocomplete/releases/tag/v1.0.0
[1.1.0]: https://github.com/sneddy/geo_autocomplete/compare/v1.0.0...v1.1.0
[2.0.0]: https://github.com/sneddy/geo_autocomplete/compare/v1.1.0...v2.0.0

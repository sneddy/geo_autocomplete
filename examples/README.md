# Reproducible consumers

The repository has three examples at different levels:

- [`custom_catalog.py`](custom_catalog.py) shows the public, domain-agnostic
  Python API with caller-owned records.
- [`dsml/`](dsml/) documents the compatibility profile used by DSML.kz.
- [`hspace/`](hspace/) documents the broader research profile used by HSpace.

The site examples are intentionally thin. They define dataset selection and
static ranking here, then leave HTTP transport, authentication, caching, and UI
state to the consuming application. This keeps the autocomplete build and
ranking reproducible without turning this repository into a web framework.

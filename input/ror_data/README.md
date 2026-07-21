# ROR source data

The university index is built from the canonical JSON file in the official
[Research Organization Registry data dump](https://ror.readme.io/docs/data-dump).
Raw releases are not committed because the JSON file exceeds GitHub's per-file
size limit.

The current release artifact uses ROR v2.10, published on 2026-07-20:

```text
v2.10-2026-07-20-ror-data.json
```

Download the release ZIP from
[Zenodo](https://zenodo.org/records/21458494), extract it into this directory,
and run:

```bash
python3 scripts/build_university_index.py
```

The builder intentionally reads JSON rather than CSV. ROR maintains JSON as
the format of record; the CSV contains only a flattened subset of fields.

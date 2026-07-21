#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from stateless_autocomplete import AutocompleteIndex, SearchDocument, SearchTerm


@dataclass(frozen=True, slots=True)
class CatalogItem:
    item_id: str
    label: str
    aliases: tuple[str, ...]
    category: str
    priority: int


CATALOG = (
    CatalogItem("conf-icml", "International Conference on Machine Learning", ("ICML",), "conference", 0),
    CatalogItem("conf-neurips", "Neural Information Processing Systems", ("NeurIPS", "NIPS"), "conference", 1),
    CatalogItem("lab-mila", "Mila - Quebec AI Institute", ("Mila",), "laboratory", 2),
)


def build_index(items: tuple[CatalogItem, ...] = CATALOG) -> AutocompleteIndex[CatalogItem]:
    return AutocompleteIndex(
        SearchDocument(
            key=item.item_id,
            label=item.label,
            payload=item,
            terms=tuple(
                SearchTerm(term)
                for term in (item.label, *item.aliases)
            ),
            priority=item.priority,
        )
        for item in items
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search a small custom catalog with the public stateless API."
    )
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    matches = build_index().search(args.query, limit=args.limit)
    print(json.dumps([asdict(item) for item in matches], indent=2))


if __name__ == "__main__":
    main()

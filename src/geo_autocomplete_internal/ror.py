from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .models import OrganizationName, ResearchOrganization


def iter_json_array(path: str | Path, *, chunk_size: int = 1 << 20) -> Iterator[Any]:
    """Stream values from a top-level JSON array without loading the dump at once."""

    decoder = json.JSONDecoder()
    buffer = ""
    position = 0
    started = False
    finished = False

    with Path(path).open(encoding="utf-8") as stream:
        while True:
            if position >= len(buffer) and not finished:
                buffer = stream.read(chunk_size)
                position = 0
                finished = not buffer

            while position < len(buffer) and buffer[position].isspace():
                position += 1

            if not started:
                if position >= len(buffer):
                    if finished:
                        raise ValueError("ROR source is empty")
                    continue
                if buffer[position] != "[":
                    raise ValueError("ROR source must contain a top-level JSON array")
                position += 1
                started = True
                continue

            while position < len(buffer) and (
                buffer[position].isspace() or buffer[position] == ","
            ):
                position += 1

            if position < len(buffer) and buffer[position] == "]":
                return

            if position >= len(buffer):
                if finished:
                    raise ValueError("ROR source ended before the JSON array was closed")
                buffer = ""
                position = 0
                continue

            try:
                value, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError as error:
                if finished:
                    raise ValueError("ROR source contains invalid JSON") from error
                chunk = stream.read(chunk_size)
                if not chunk:
                    finished = True
                buffer = buffer[position:] + chunk
                position = 0
                continue

            yield value
            position = end
            if position >= chunk_size:
                buffer = buffer[position:]
                position = 0


def _required_string(record: dict[str, Any], field: str, index: int) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"ROR record {index}: required field {field!r} is empty")
    return value.strip()


def _parse_organization(record: dict[str, Any], index: int) -> ResearchOrganization:
    raw_names = record.get("names") or []
    names = tuple(
        OrganizationName(
            value=str(name["value"]).strip(),
            types=tuple(str(value) for value in name.get("types") or []),
            language=str(name["lang"]) if name.get("lang") else None,
        )
        for name in raw_names
        if isinstance(name, dict) and str(name.get("value") or "").strip()
    )
    if not names:
        raise ValueError(f"ROR record {index}: no usable names")

    locations = record.get("locations") or []
    if not locations:
        raise ValueError(f"ROR record {index}: no location")
    location = locations[0]
    details = location.get("geonames_details") or {}

    website = next(
        (
            str(link.get("value") or "").strip()
            for link in record.get("links") or []
            if link.get("type") == "website" and link.get("value")
        ),
        "",
    )
    established = record.get("established")
    return ResearchOrganization(
        ror_id=_required_string(record, "id", index),
        names=names,
        status=_required_string(record, "status", index),
        types=tuple(str(value) for value in record.get("types") or []),
        country=str(details.get("country_name") or "").strip(),
        country_code=str(details.get("country_code") or "").strip(),
        city=str(details.get("name") or "").strip(),
        admin_name=str(details.get("country_subdivision_name") or "").strip(),
        geonames_id=int(location["geonames_id"]),
        lat=float(details["lat"]),
        lng=float(details["lng"]),
        established=int(established) if established is not None else None,
        domains=tuple(
            str(domain).strip()
            for domain in record.get("domains") or []
            if str(domain).strip()
        ),
        website=website,
    )


def load_ror_organizations(
    path: str | Path,
    *,
    active_only: bool = True,
    organization_types: frozenset[str] | None = frozenset({"education"}),
) -> list[ResearchOrganization]:
    """Load a filtered organization set from the canonical ROR JSON dump."""

    organizations: list[ResearchOrganization] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(iter_json_array(path), start=1):
        if not isinstance(value, dict):
            raise ValueError(f"ROR record {index}: expected an object")
        status = value.get("status")
        types = frozenset(str(item) for item in value.get("types") or [])
        if active_only and status != "active":
            continue
        if organization_types is not None and not organization_types.intersection(types):
            continue
        organization = _parse_organization(value, index)
        if organization.ror_id in seen_ids:
            raise ValueError(f"ROR record {index}: duplicate ID {organization.ror_id}")
        seen_ids.add(organization.ror_id)
        organizations.append(organization)
    return organizations

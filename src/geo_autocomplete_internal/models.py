from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class City:
    city: str
    city_ascii: str
    lat: float
    lng: float
    country: str
    iso2: str
    iso3: str
    admin_name: str
    capital: str
    population: int | None
    source_id: int
    city_ru: str = ""
    country_ru: str = ""
    priority: int | None = None
    ranking_score: float | None = None
    ranking_reasons: tuple[str, ...] = ()

    @property
    def translation_key(self) -> tuple[str, str]:
        return self.iso2, self.city_ascii.casefold()

    def translated(self, city_ru: str = "", country_ru: str = "") -> City:
        return replace(self, city_ru=city_ru, country_ru=country_ru)

    def ranked(self, priority: int, score: float | None, reasons: tuple[str, ...]) -> City:
        return replace(
            self,
            priority=priority,
            ranking_score=score,
            ranking_reasons=reasons,
        )


@dataclass(frozen=True, slots=True)
class TranslationCatalog:
    cities: dict[tuple[str, str], str]
    countries: dict[str, str]

    def apply(self, city: City) -> City:
        return city.translated(
            city_ru=self.cities.get(city.translation_key, ""),
            country_ru=self.countries.get(city.iso2, ""),
        )


@dataclass(frozen=True, slots=True)
class OrganizationName:
    value: str
    types: tuple[str, ...]
    language: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchOrganization:
    ror_id: str
    names: tuple[OrganizationName, ...]
    status: str
    types: tuple[str, ...]
    country: str
    country_code: str
    city: str
    admin_name: str
    geonames_id: int
    lat: float
    lng: float
    established: int | None = None
    domains: tuple[str, ...] = ()
    website: str = ""
    priority: int | None = None
    ranking_score: float | None = None
    ranking_reasons: tuple[str, ...] = ()

    @property
    def display_name(self) -> str:
        for name in self.names:
            if "ror_display" in name.types:
                return name.value
        return self.names[0].value

    def names_of_type(self, name_type: str) -> tuple[str, ...]:
        return tuple(
            name.value for name in self.names if name_type in name.types
        )

    @property
    def all_names(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(name.value for name in self.names))

    def ranked(
        self, priority: int, score: float, reasons: tuple[str, ...]
    ) -> ResearchOrganization:
        return replace(
            self,
            priority=priority,
            ranking_score=score,
            ranking_reasons=reasons,
        )

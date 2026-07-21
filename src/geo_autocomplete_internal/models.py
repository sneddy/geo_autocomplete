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

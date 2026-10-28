from dataclasses import dataclass
from typing import Any, Protocol


class CountryReferenceUnavailable(Exception):
    pass


@dataclass(frozen=True)
class CountryCatalogue:
    version: str
    sha256: str
    countries: tuple[dict[str, str], ...]
    attribution: dict[str, Any]

    def contains(self, code):
        return any(country["code"] == code for country in self.countries)

    def reference(self):
        return {"source": "GeoNames countryInfo", "release": self.version, "sha256": self.sha256}

    def public(self):
        return {"version": self.version, "countries": list(self.countries), "attribution": self.attribution}


class CountryReference(Protocol):
    def load(self) -> CountryCatalogue: ...

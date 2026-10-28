from dataclasses import dataclass
from typing import Any, Protocol
from unicodedata import normalize


class LocalityReferenceUnavailable(Exception):
    pass


@dataclass(frozen=True)
class LocalityCatalogue:
    version: str
    sha256: str
    snapshot_at: str
    rows: tuple[dict[str, Any], ...]
    attribution: dict[str, Any]

    def supports(self, country):
        return country in ("CH", "LI")

    def matches(self, country, town=None, postcode=None):
        if not self.supports(country):
            return ()
        name = normalize("NFC", town.strip()).casefold() if town is not None else None
        postal = postcode.strip() if postcode is not None else None
        return tuple(row for row in self.rows if row["country_code"] == country
            and (name is None or row["matching"]["locality_name"] == name)
            and (postal is None or row["matching"]["postcode"] == postal))

    def reference(self):
        return {"source": "swisstopo", "release": self.version, "sha256": self.sha256,
            "snapshot_at": self.snapshot_at}

    def association(self, row):
        return {"reference": {"source": "swisstopo", "release": self.version,
                "source_record": row["source_record"]},
            **{key: row[key] for key in ("country_code", "locality_name", "postcode",
                "source_postcode_id", "additional_number")},
            "administrative": dict(row["administrative"])}

    def selected(self, pointer):
        if (not isinstance(pointer, dict) or set(pointer) != {"source", "release", "source_record"}
                or pointer["source"] != "swisstopo" or pointer["release"] != self.version
                or type(pointer["source_record"]) is not int):
            return None
        return next((row for row in self.rows if row["source_record"] == pointer["source_record"]), None)


class LocalityReference(Protocol):
    def load(self) -> LocalityCatalogue: ...

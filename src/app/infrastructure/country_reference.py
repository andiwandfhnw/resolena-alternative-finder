from hashlib import sha256
import json
from pathlib import Path
import re

from app.application.countries import CountryCatalogue, CountryReferenceUnavailable


ROOT = Path(__file__).resolve().parents[3]
RELEASE = "geonames-countryInfo-2026-10-23-v1"
SOURCE_SHA256 = "c55f638cfaafb4fe45a9aa15120a0f1f78e8a34a8e1847d7b9320cf740fbc9ab"
CATALOGUE_SHA256 = "8044346fd37ccc6fa1fa99da3068bb69c9bb987bc6ac7a96f04b3618940fe885"
APPROVAL_SCOPE = "Priority 5R development slice and isolated demo/test composition only"


class LocalCountryCatalogue:
    def __init__(self, manifest_path=None, catalogue_path=None):
        self.manifest_path = Path(manifest_path) if manifest_path else ROOT / "docs/reference/COUNTRIES-GEONAMES-2026-10-23-MANIFEST.json"
        self.catalogue_path = Path(catalogue_path) if catalogue_path else ROOT / "docs/reference/COUNTRIES-GEONAMES-2026-10-23.json"

    def load(self):
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            raw = self.catalogue_path.read_bytes()
            countries = json.loads(raw)
            approval = manifest["approval"]
            if (manifest["release_id"] != RELEASE or manifest["status"] != "approved-development"
                    or manifest["runtime_use"] != "development-only"
                    or approval["owner_approved"] is not True or approval["approved_on"] != "2026-10-23"
                    or approval["scope"] != APPROVAL_SCOPE or approval["production_activation_approved"] is not False
                    or approval["independent_factual_review"] is not False or approval["linguistic_approval"] is not False
                    or manifest["raw_source"]["sha256"] != SOURCE_SHA256
                    or manifest["normalized_output"]["sha256"] != CATALOGUE_SHA256
                    or sha256(raw).hexdigest() != CATALOGUE_SHA256):
                raise ValueError("Country release is not the approved development reference")
            if (not isinstance(countries, list) or len(countries) != 250
                    or any(set(country) != {"code", "name"} or not re.fullmatch(r"[A-Z]{2}", country["code"])
                        or not country["name"].strip() for country in countries)
                    or len({country["code"] for country in countries}) != len(countries)):
                raise ValueError("Invalid country extract")
            attribution = manifest["attribution"]
            if (attribution["source_link"] != "https://download.geonames.org/export/dump/countryInfo.txt"
                    or attribution["license_link"] != "https://creativecommons.org/licenses/by/4.0/"
                    or not all(isinstance(attribution[key], str) and attribution[key].strip()
                        for key in ("credit", "license", "changes", "disclaimer"))):
                raise ValueError("Missing country attribution")
            return CountryCatalogue(RELEASE, CATALOGUE_SHA256, tuple(countries), attribution)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CountryReferenceUnavailable from error

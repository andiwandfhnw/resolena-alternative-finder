from hashlib import sha256
import json
from pathlib import Path

from app.application.localities import LocalityCatalogue, LocalityReferenceUnavailable


ROOT = Path(__file__).resolve().parents[3]
RELEASE = "swisstopo-chli-associations-2026-10-01-v1"
SOURCE_SHA256 = "0903076e7c3b8670d836ec20d486f9d2045b120e61f07d27a2bd7be09443098b"
CATALOGUE_SHA256 = "eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9"
SNAPSHOT_AT = "2026-10-01T00:00:00Z"
APPROVAL_SCOPE = "Priority 5U development slice and isolated demo/test composition only"
PRODUCT = "https://www.swisstopo.admin.ch/en/official-directory-of-towns-and-cities"
TERMS = "https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices"


class LocalLocalityCatalogue:
    def __init__(self, manifest_path=None, catalogue_path=None):
        self.manifest_path = Path(manifest_path) if manifest_path else ROOT / "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-APPROVAL.json"
        self.catalogue_path = Path(catalogue_path) if catalogue_path else ROOT / "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01.json"

    def load(self):
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            raw = self.catalogue_path.read_bytes()
            approval = manifest["approval"]
            if (manifest["release_id"] != RELEASE or manifest["status"] != "approved-development"
                    or manifest["runtime_use"] != "development-only"
                    or approval["owner_approved"] is not True or approval["approved_on"] != "2026-10-23"
                    or approval["scope"] != APPROVAL_SCOPE or approval["production_activation_approved"] is not False
                    or approval["independent_factual_review"] is not False or approval["linguistic_approval"] is not False
                    or manifest["raw_source"]["sha256"] != SOURCE_SHA256
                    or manifest["normalized_output"]["sha256"] != CATALOGUE_SHA256
                    or manifest["source_dates"]["snapshot_at"] != SNAPSHOT_AT
                    or sha256(raw).hexdigest() != CATALOGUE_SHA256):
                raise ValueError("Locality release is not the approved development reference")
            rows = json.loads(raw)
            if (not isinstance(rows, list) or len(rows) != 5716
                    or [row["source_record"] for row in rows] != list(range(1, 5717))
                    or any(set(row) != {"source_record", "country_code", "locality_name", "postcode",
                        "source_postcode_id", "additional_number", "administrative", "matching"}
                        or row["country_code"] not in ("CH", "LI")
                        or any(not isinstance(row[key], str) or not row[key].strip()
                            for key in ("locality_name", "postcode", "source_postcode_id", "additional_number"))
                        or set(row["administrative"]) != {"municipality_name", "municipality_id", "canton"}
                        or set(row["matching"]) != {"locality_name", "postcode"} for row in rows)):
                raise ValueError("Invalid locality association extract")
            attribution = manifest["attribution"]
            if (attribution["source_reference"] != PRODUCT or attribution["terms_reference"] != TERMS
                    or not all(isinstance(attribution[key], str) and attribution[key].strip()
                        for key in ("credit", "basis", "modification_notice"))):
                raise ValueError("Missing locality attribution")
            return LocalityCatalogue(RELEASE, CATALOGUE_SHA256, SNAPSHOT_AT, tuple(rows), attribution)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise LocalityReferenceUnavailable from error

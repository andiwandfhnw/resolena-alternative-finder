"""Offline integrity checks and current-worktree handoff; never starts inference."""

import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import stat
from zipfile import ZIP_DEFLATED, ZipFile


PACKAGE = "scripts/uc001_granite_contract_v1"
PACKAGE_FILES = ("prompt.txt", "system-prompt.txt", "wire-schema.json", "schema.json",
    "config.json", "cases.json", "validation-dependencies.json", "approval-template.json",
    "review-template.json", "schema-audit.md", "README.md", "package.py", "assess.py",
    "native-inspection/inspect-schema.cpp", "native-inspection/CMakeLists.txt")
MAX_TRANSFER = 32 * 1024 * 1024


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def safe_path(root, name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name
            or any(part.startswith(".") or part in ("experiments", "__pycache__", "held_out", "held-out") for part in path.parts)
            or path.suffix not in (".py", ".json", ".md", ".txt", ".toml", ".cpp")):
        raise ValueError("Unsafe or private transfer path")
    root = Path(root).resolve()
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlinks cannot enter the handoff")
    if not current.resolve().is_relative_to(root) or not current.is_file():
        raise ValueError("Missing or external transfer file")
    return current


def freeze_files(root, names):
    names = sorted(names)
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("Duplicate transfer identity")
    files = {}
    for name in names:
        raw = safe_path(root, name).read_bytes()
        files[name] = {"sha256": sha256(raw).hexdigest(), "bytes": len(raw)}
    if sum(item["bytes"] for item in files.values()) > MAX_TRANSFER:
        raise ValueError("Handoff exceeds the explicit size bound")
    return {"version": "uc001-granite-freeze-v1", "bundle_id": sha256(canonical(files)).hexdigest(), "files": files}


def verify_files(root, frozen):
    if freeze_files(root, frozen["files"]) != frozen:
        raise ValueError("Frozen current-worktree files changed")


def write_archive(root, frozen, output):
    verify_files(root, frozen)
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for name in frozen["files"]:
            archive.writestr(name, safe_path(root, name).read_bytes())
        archive.writestr(PACKAGE + "/freeze.json", canonical(frozen) + b"\n")


def verify_archive(path, frozen):
    with ZipFile(path) as archive:
        members = archive.infolist()
        names = [member.filename for member in members]
        expected = set(frozen["files"]) | {PACKAGE + "/freeze.json"}
        if (len(set(names)) != len(names) or set(names) != expected
                or sum(member.file_size for member in members) > MAX_TRANSFER + 1024 * 1024
                or any(stat.S_ISLNK(member.external_attr >> 16) for member in members)):
            raise ValueError("Unexpected, duplicate or oversized archive members")
        for name, metadata in frozen["files"].items():
            raw = archive.read(name)
            if len(raw) != metadata["bytes"] or sha256(raw).hexdigest() != metadata["sha256"]:
                raise ValueError("Transferred bytes do not match the freeze")
        if json.loads(archive.read(PACKAGE + "/freeze.json")) != frozen:
            raise ValueError("Transferred freeze changed")


def reserve_generation(ledger, case_id, case_ids, bundle_id):
    attempts = ledger["generation_attempts"]
    if (ledger["bundle_id"] != bundle_id or ledger["closed"] is not False
            or len(attempts) >= 11 or len(attempts) >= len(case_ids)
            or attempts != case_ids[:len(attempts)] or case_id != case_ids[len(attempts)]):
        raise ValueError("No retry, reordering, continuation or extra inference is allowed")
    attempts.append(case_id)


def check_approval(approval, bundle_id):
    if (approval.get("bundle_id") != bundle_id or not approval.get("owner") or not approval.get("authorized_on")
            or any(approval.get(key) is not True for key in ("acquisition_approved", "build_approved",
                "live_execution_approved", "desktop_prerequisites_and_resource_supervision_confirmed"))
            or type(approval.get("maximum_startups")) is not int or approval["maximum_startups"] != 1
            or type(approval.get("maximum_generations")) is not int or approval["maximum_generations"] != 11):
        raise ValueError("Separate explicit owner authorization and desktop readiness are required")


def accept_review(review, bundle_id, case_id, packet_sha256):
    if (review.get("bundle_id") != bundle_id or review.get("case_id") != case_id
            or review.get("packet_sha256") != packet_sha256 or review.get("semantic_status") != "pass"
            or review.get("qualified_review_status") != "confirmed" or not review.get("reviewer")
            or not review.get("competence_basis")):
        raise ValueError("Meaning failure or unavailable competent review cannot pass")


def sources(root):
    root = Path(root)
    names = {path.relative_to(root).as_posix() for path in (root / "src/app").glob("**/*.py")}
    names.update(PACKAGE + "/" + name for name in PACKAGE_FILES)
    names.update(("tests/__init__.py", "tests/support/__init__.py", "tests/support/synthetic.py",
        "scripts/uc001_contract_check/development.py", "pyproject.toml", "requirements.txt",
        "docs/reference/COUNTRIES-GEONAMES-2026-10-23.json",
        "docs/reference/COUNTRIES-GEONAMES-2026-10-23-MANIFEST.json",
        "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01.json",
        "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-APPROVAL.json"))
    return sorted(names)


def validate_cases(root):
    value = json.loads((Path(root) / PACKAGE / "cases.json").read_text(encoding="utf-8"))
    cases = value["cases"]
    if len(cases) != 11 or [case["order"] for case in cases] != list(range(1, 12)) or len({case["id"] for case in cases}) != 11:
        raise ValueError("Exactly eleven fixed exposed cases are required")
    for case in cases:
        raw = case["text"].encode()
        if (raw != b64decode(case["input_utf8_base64"], validate=True) or len(raw) != case["input_utf8_bytes"]
                or sha256(raw).hexdigest() != case["input_utf8_sha256"]):
            raise ValueError("Exposed input bytes changed")
    return value


def load_frozen(root):
    frozen = json.loads((Path(root) / PACKAGE / "freeze.json").read_text(encoding="utf-8"))
    if set(frozen["files"]) != set(sources(root)):
        raise ValueError("Required current code/reference closure changed")
    verify_files(root, frozen)
    validate_cases(root)
    return frozen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "verify", "transfer", "verify-archive"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.command == "freeze":
        validate_cases(root)
        frozen = freeze_files(root, sources(root))
        (root / PACKAGE / "freeze.json").write_bytes(canonical(frozen) + b"\n")
    else:
        frozen = load_frozen(root)
        if args.command == "transfer":
            if args.output is None:
                parser.error("--output is required")
            write_archive(root, frozen, args.output)
            verify_archive(args.output, frozen)
        elif args.command == "verify-archive":
            if args.archive is None:
                parser.error("--archive is required")
            verify_archive(args.archive, frozen)
    print(json.dumps({"command": args.command, "bundle_id": frozen["bundle_id"], "files": len(frozen["files"]), "inference": False}))


if __name__ == "__main__":
    main()

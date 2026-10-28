"""Offline documentation, frozen-file and Git preservation checks only."""

from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
PACKAGE = ROOT / "scripts/uc001_granite_contract_v1"


def git(*arguments):
    return subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True)


baseline = json.loads((BASE / "preservation-baseline.json").read_text())
changed = [name for name, digest in baseline.items()
    if not (ROOT / name).is_file() or sha256((ROOT / name).read_bytes()).hexdigest() != digest]
assert changed == ["docs/TASKS.md"], changed
tasks = (ROOT / "docs/TASKS.md").read_text()
before = (BASE / "before/docs/TASKS.md").read_text()
assert tasks.startswith("PHASE: 3\nSTATUS: in-progress\n")
marker = "Current Priority 5 work-package status:"
assert tasks.split(marker, 1)[1] == before.split(marker, 1)[1]
new_entry = tasks.split("### Priority 3 — provisional Granite offline preparation, 2026-10-25", 1)[1].split(marker, 1)[0]
links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", new_entry)
for name in links:
    assert (ROOT / "docs" / name).resolve().is_file(), name
json_files = sorted(PACKAGE.glob("*.json")) + [BASE / "verification.json", BASE / "commands.json"]
for path in json_files:
    json.loads(path.read_text())
config = json.loads((PACKAGE / "config.json").read_text())
readme = (PACKAGE / "README.md").read_text()
server_line = next(line for line in readme.splitlines() if line.startswith("$GraniteServerArgs = @("))
tokens = re.findall(r"'([^']*)'|(\$[A-Za-z0-9_]+)", server_line.split("@(", 1)[1])
arguments = [literal or {"$GraniteModel": "{model_file}", "$GraniteKeyFile": "{private_api_key_file}"}[variable]
    for literal, variable in tokens]
assert arguments == config["server_arguments"]
whitespace = []
for path in [*PACKAGE.rglob("*"), ROOT / "src/app/infrastructure/granite_interpreter.py",
        ROOT / "tests/integration/test_granite_contract_adapter.py", ROOT / "tests/unit/test_granite_package.py"]:
    if path.is_file() and "__pycache__" not in path.parts:
        whitespace.extend(f"{path.relative_to(ROOT)}:{number}" for number, line in enumerate(path.read_text().splitlines(), 1)
            if line.rstrip() != line)
assert not whitespace, whitespace
head = git("rev-parse", "HEAD")
branch = git("branch", "--show-current")
index = git("ls-files", "--stage")
status = git("status", "--short")
diff_check = git("diff", "--check")
for result in (head, branch, index, status):
    assert result.returncode == 0, result.stderr
assert head.stdout == (BASE / "git-head-before.txt").read_text()
assert branch.stdout == (BASE / "git-branch-before.txt").read_text()
assert index.stdout == (BASE / "git-index-before.txt").read_text()
assert diff_check.returncode == 2
assert diff_check.stdout.count("trailing whitespace") == 1
assert "+  evidence-backed comparisons and persistence. \n" in diff_check.stdout
(BASE / "git-status.txt").write_text(status.stdout)
(BASE / "git-head.txt").write_text(head.stdout)
(BASE / "git-branch.txt").write_text(branch.stdout)
(BASE / "git-index.txt").write_text(index.stdout)
(BASE / "git-diff-check.txt").write_text(diff_check.stdout + diff_check.stderr)
report = {"protected_files": len(baseline), "unchanged_protected_files": len(baseline) - len(changed),
    "authorized_existing_changes": changed, "priority5_status_and_all_following_history_unchanged": True,
    "head_unchanged": head.stdout.strip(), "branch_unchanged": branch.stdout.strip(), "index_unchanged": True,
    "phase": 3, "status": "in-progress", "new_task_links_checked": links,
    "json_files_parsed": len(json_files), "readme_server_arguments_match_frozen_config": True,
    "new_file_whitespace_errors": whitespace, "git_diff_check_exit_code": diff_check.returncode,
    "git_diff_check": diff_check.stdout, "historical_whitespace_warning_preserved": True}
(BASE / "preservation-check.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))

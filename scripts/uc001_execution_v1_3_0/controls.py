from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import time


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[1]


def load_bundle(root=ROOT):
    root = Path(root)
    freeze = json.loads((root / "freeze.json").read_text())
    for base, group in ((root, "files"), (REPOSITORY, "application_files")):
        for name, expected in freeze[group].items():
            if sha256((base / name).read_bytes()).hexdigest() != expected:
                raise ValueError("Frozen preparation mismatch: " + name)
    return {"config": json.loads((root / "config.json").read_text()),
        "cases": json.loads((root / "cases.json").read_text()), "freeze": freeze,
        "freeze_sha256": sha256((root / "freeze.json").read_bytes()).hexdigest(),
        "prompt": (root / "prompt.txt").read_text()}


def verify_effective(props, log):
    generation = props["default_generation_settings"]
    if (props["total_slots"] != 1 or generation["n_ctx"] != 8192
            or not re.fullmatch(r"b11429-d81235049[0-9a-f]*", props["build_info"])
            or props["model_path"] != r"C:\ResolenaExperiments\qwen3-8b-v1\Qwen3-8B-Q8_0.gguf"):
        raise ValueError("Effective runtime/model/context/slot mismatch")
    from app.infrastructure.llama_cpp_interpreter import LlamaCppInterpreter
    for field, expected in {"n_predict": 3072, **LlamaCppInterpreter.SAMPLING}.items():
        if not math.isclose(generation["params"][field], expected, abs_tol=1e-6):
            raise ValueError("Effective sampling/output mismatch: " + field)
    patterns = [r"build 11429 \(d81235049\)", r"using device Vulkan0 \(AMD Radeon RX 6800 XT\)",
        r"offloaded 37/37 layers to GPU", r"n_threads = 2 \(n_threads_batch = 2\)",
        r"n_ctx_seq\s*=\s*8192\b", r"n_batch\s*=\s*64\b", r"n_ubatch\s*=\s*64\b",
        r"K \(f16\):.*V \(f16\):"]
    if any(not re.search(pattern, log) for pattern in patterns):
        raise ValueError("Current startup log does not establish full Vulkan offload/settings")


@dataclass
class RunBudget:
    path: Path
    order: list
    deadline: float
    clock: object = time.time

    def __post_init__(self):
        self.index = 0
        self.path.open("x").close()

    def consume(self, identity):
        if self.clock() >= self.deadline:
            raise TimeoutError("Fixed execution deadline expired")
        if self.index >= len(self.order) or identity != self.order[self.index]:
            raise ValueError("No retry, extra generation or reordered case is permitted")
        with self.path.open("a") as output:
            output.write(json.dumps({"attempt": self.index + 1, "case": identity, "time": self.clock()}) + "\n")
            output.flush()
            os.fsync(output.fileno())
        self.index += 1


def check_case_state(case, result):
    # These checks enforce explicit packet declarations, not all semantic expectations.
    if result["meaning_status"] not in case["allowed_meaning_states"]:
        raise ValueError("Declared meaning state violates the frozen case boundary")
    if case["id"] == 1 and (result["recognition"] != {"status": "unsupported", "language": None}
            or not result.get("message")):
        raise ValueError("Unsupported control repeated the known capability-routing failure")
    if case.get("required_unresolved_quantity") and result["meaning_status"] == "understood":
        quantities = [item.get("quantity") for item in result.get("items", []) if item["kind"] == "budget"]
        if len(quantities) != 1 or quantities[0] is None or quantities[0]["amount"] is not None:
            raise ValueError("Ambiguous numeric magnitude was guessed or omitted")


def verify_authentication(client):
    for credential in (None, "Bearer deliberately-invalid"):
        request = client.build_request("GET", "/v1/models")
        if credential is None:
            request.headers.pop("Authorization", None)
        else:
            request.headers["Authorization"] = credential
        if client.send(request).status_code != 401:
            raise ValueError("Protected endpoint accepted missing/wrong authentication")
    response = client.get("/v1/models")
    response.raise_for_status()
    if [model["id"] for model in response.json()["data"]] != ["uc001-qwen3-8b"]:
        raise ValueError("Valid authentication did not reach the owned model alias")

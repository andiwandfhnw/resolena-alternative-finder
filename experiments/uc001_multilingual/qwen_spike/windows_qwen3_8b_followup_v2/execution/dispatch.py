"""Offline checkpoint assessment; no network, model, or Windows process access."""
import argparse
import hashlib
import json
import math
import re
import stat
import statistics
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from assess import classify, schema_errors
from contract import SCHEMA

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def obj(data):
    return json.loads(data.decode("utf-8-sig"))


def instant(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("UTC offset required")
    return result


class Bundle:
    def __init__(self, root, freeze_bytes):
        self.root = root
        self.freeze_sha = sha(freeze_bytes)
        self.freeze = obj(freeze_bytes)
        for name, expected in self.freeze["files"].items():
            if sha((root / name).read_bytes()) != expected:
                raise ValueError("Frozen payload changed: " + name)
        self.config = obj((root / "config.json").read_bytes())
        self.order = obj((root / "order.json").read_bytes())
        self.cases = {c["id"]: c for c in obj((root / "cases.json").read_bytes())}
        provenance = obj((root / "provenance.json").read_bytes())
        for name, field in [("contract.py", "unchanged_contract_sha256"), ("assess.py", "unchanged_assessor_sha256")]:
            if sha((root / name).read_bytes()) != provenance[field]:
                raise ValueError("Original scorer changed: " + name)

    def request_hash(self, entry):
        return sha((self.root / entry["request"]).read_bytes())


def read_archive(path):
    files = {}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > 600 or sum(i.file_size for i in infos) > 64 * 1024 * 1024:
            raise ValueError("Archive exceeds small-result limits")
        for info in infos:
            name = info.filename.replace("\\", "/")
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or ":" in name or stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1:
                raise ValueError("Unsafe archive member")
            if info.is_dir():
                continue
            if name in files:
                raise ValueError("Duplicate normalized archive member")
            files[name] = archive.read(info)
    return files


def validate_checkpoint(bundle, files):
    if sha(files["freeze.json"]) != bundle.freeze_sha:
        raise ValueError("Wrong freeze")
    run, checkpoint = obj(files["run.json"]), obj(files["checkpoint.json"])
    if run["freeze_sha256"] != bundle.freeze_sha or checkpoint["freeze_sha256"] != bundle.freeze_sha:
        raise ValueError("Freeze binding")
    if checkpoint["run_id"] != run["run_id"] or checkpoint["deadline_utc"] != run["deadline_utc"] or not checkpoint["nonce"]:
        raise ValueError("Run/deadline/nonce binding")
    if (instant(run["deadline_utc"]) - instant(run["started_utc"])).total_seconds() != 1800:
        raise ValueError("Window changed")
    count = len(checkpoint["completed_ids"])
    if count not in bundle.config["checkpoint_after_indices"] or checkpoint["checkpoint_id"] != f"cp{count:02d}":
        raise ValueError("Unexpected checkpoint")
    entries = bundle.order[:count]
    if checkpoint["completed_ids"] != [p["id"] for p in entries] or len(checkpoint["receipts"]) != count:
        raise ValueError("Non-prefix order or skipped request")
    for entry, receipt in zip(entries, checkpoint["receipts"]):
        for key in ["id", "case", "arm"]:
            if receipt[key] != entry[key]:
                raise ValueError("Arm/case/order receipt binding")
        request = files[entry["request"]]
        response = files["responses/" + entry["id"] + ".json"]
        if sha(request) != bundle.request_hash(entry) or receipt["request_sha256"] != sha(request) or receipt["response_sha256"] != sha(response):
            raise ValueError("Request/response checksum binding")
        record = obj(response)
        expected = {"run_id": run["run_id"], "bundle_freeze_sha256": bundle.freeze_sha,
            "request_id": entry["id"], "case": entry["case"], "arm": entry["arm"], "request_sha256": sha(request)}
        if any(record.get(k) != v for k, v in expected.items()):
            raise ValueError("Response arm/request/freeze binding")
    return run, checkpoint, entries


def runtime_errors(bundle, files):
    errors = []
    log = files.get("server.stderr.log", b"").decode("utf-8-sig", errors="replace")
    layers = re.findall(r"offloaded (\d+)/(\d+) layers to GPU", log)
    if not layers or any(int(n) != int(total) or int(n) <= 0 for n, total in layers):
        errors.append("offload_layers_unconfirmed")
    if not re.search(r"Vulkan0.*model buffer size", log):
        errors.append("vulkan_model_buffer_unconfirmed")
    if not re.search(r"Vulkan0.*RX\s*6800\s*XT", log):
        errors.append("vulkan_device_unconfirmed")
    kv = re.search(r"Vulkan0.*KV buffer size\s*=\s*([0-9.]+)\s*MiB", log)
    if not kv or float(kv[1]) <= 0:
        errors.append("vulkan_kv_buffer_unconfirmed")
    samples = [obj(line) for line in files.get("resources.jsonl", b"").splitlines() if line.strip()]
    if not any(s.get("owned_gpu_bytes", 0) > 0 for s in samples):
        errors.append("owned_gpu_allocation_unconfirmed")
    limits = bundle.config["limits"]
    for s in samples:
        for field, threshold, maximum in [("owned_rss_bytes", "rss_bytes", True), ("owned_gpu_bytes", "gpu_owned_bytes", True),
                ("scratch_bytes", "scratch_bytes", True), ("available_ram_bytes", "ram_floor_bytes", False),
                ("adapter_free_bytes", "gpu_floor_bytes", False), ("disk_free_bytes", "disk_floor_bytes", False)]:
            value = s.get(field)
            if not isinstance(value, (int, float)) or (value > limits[threshold] if maximum else value < limits[threshold]):
                errors.append("resource:" + field)
    if "guard_failure.json" in files:
        errors.append("resource_or_deadline_guard")
    capacity = obj(files.get("capacity.json", b"{}"))
    if capacity.get("context") != 2048 or capacity.get("output_tokens") != 384:
        errors.append("context_or_output_limit")
    for entry in bundle.order:
        proof = capacity.get("requests", {}).get(entry["id"], {})
        tokens = proof.get("tokens")
        if proof.get("request_sha256") != bundle.request_hash(entry) or proof.get("nonthinking") is not True or not isinstance(tokens, int) or tokens < 1 or tokens + 384 > 2048:
            errors.append("capacity:" + entry["id"])
    return errors


def evaluate(bundle, entry, files):
    record = obj(files["responses/" + entry["id"] + ".json"])
    operational = []
    if record.get("http_status") != 200 or record.get("transport_error"):
        operational.append("http_or_transport")
    if not isinstance(record.get("wall_seconds"), (int, float)) or record["wall_seconds"] > 45:
        operational.append("request_timeout")
    result = {"strict_pass": False}
    try:
        raw = json.loads(record["raw_body"])
        choice = raw["choices"][0]
        if choice.get("finish_reason") != "stop":
            operational.append("finish_reason")
        if choice["message"].get("reasoning_content"):
            operational.append("thinking_output")
        usage, timings = raw.get("usage", {}), raw.get("timings", {})
        if not usage or not timings:
            operational.append("missing_server_usage_or_timings")
        if timings.get("cache_n") != 0 or usage.get("prompt_tokens_details", {}).get("cached_tokens") != 0:
            operational.append("cache_not_confirmed_zero")
        try:
            output = json.loads(choice["message"]["content"])
            shape = schema_errors(output, SCHEMA)
            result = classify(bundle.cases[entry["case"]], output) if not shape else {"strict_pass": False, "schema_errors": shape}
        except (ValueError, TypeError, KeyError, IndexError) as error:
            result = {"strict_pass": False, "content_parse_failure": str(error)}
        result.update(finish_reason=choice.get("finish_reason"), usage=usage, timings=timings)
    except (ValueError, KeyError, TypeError, IndexError) as error:
        operational.append("wire_response_parse_failure")
        result["wire_parse_failure"] = str(error)
    result.update(id=entry["id"], arm=entry["arm"], case=entry["case"], stage=entry["stage"],
        wall_seconds=record.get("wall_seconds"), operational_errors=operational)
    result["strict_pass"] = bool(result["strict_pass"]) and not operational
    return result


def assess_packet(bundle, files, now):
    run, checkpoint, entries = validate_checkpoint(bundle, files)
    errors = runtime_errors(bundle, files)
    if now >= instant(run["deadline_utc"]):
        errors.append("deadline_expired")
    evaluations = [evaluate(bundle, p, files) for p in entries]
    allowed = not errors and all(not e["operational_errors"] for e in evaluations) and all(e["strict_pass"] for e in evaluations if e["arm"] == "v2")
    latencies = {}
    for arm in ["v1", "v2"]:
        values = [e["wall_seconds"] for e in evaluations if e["arm"] == arm and e["stage"] == "fresh" and isinstance(e["wall_seconds"], (int, float))]
        latencies[arm] = {"fresh_n": len(values), "fresh_median_seconds": statistics.median(values) if values else None,
            "fresh_p95_seconds": sorted(values)[math.ceil(.95 * len(values)) - 1] if values else None}
    assessment = {"version": "2.0.0", "run_id": run["run_id"], "freeze_sha256": bundle.freeze_sha,
        "checkpoint_id": checkpoint["checkpoint_id"], "checkpoint_sha256": sha(files["checkpoint.json"]),
        "classification": "AI-assisted exploratory; synthetic expectations, qualified linguistic validation pending",
        "evaluations": evaluations, "operational_errors": errors, "allowed": allowed,
        "v2_strict_passes": sum(e["strict_pass"] for e in evaluations if e["arm"] == "v2"),
        "v1_request_count": sum(e["arm"] == "v1" for e in evaluations), "latency_by_arm": latencies,
        "GPU_acceleration_established": False, "DESIGN": "pending", "linguistic_validation": "pending"}
    receipt = {"version": "2.0.0", "run_id": run["run_id"], "freeze_sha256": bundle.freeze_sha,
        "checkpoint_id": checkpoint["checkpoint_id"], "checkpoint_sha256": sha(files["checkpoint.json"]),
        "nonce": checkpoint["nonce"], "deadline_utc": run["deadline_utc"], "created_utc": now.isoformat(),
        "allowed": allowed, "next_index": len(entries) + 1,
        "assessment_sha256": sha(encoded(assessment)), "receipts": checkpoint["receipts"],
        "reason": "continue exact frozen order" if allowed else "STOP: strict v2 or operational failure; no retry"}
    return assessment, receipt


def verify_receipt(bundle, files, assessment, receipt, now):
    run, checkpoint, entries = validate_checkpoint(bundle, files)
    if now >= instant(run["deadline_utc"]):
        raise ValueError("Deadline expired; receipt cannot extend window")
    expected = {"run_id": run["run_id"], "freeze_sha256": bundle.freeze_sha, "checkpoint_id": checkpoint["checkpoint_id"],
        "checkpoint_sha256": sha(files["checkpoint.json"]), "nonce": checkpoint["nonce"],
        "deadline_utc": run["deadline_utc"], "next_index": len(entries) + 1,
        "assessment_sha256": sha(encoded(assessment)), "receipts": checkpoint["receipts"]}
    if any(receipt.get(k) != v for k, v in expected.items()) or type(receipt.get("allowed")) is not bool:
        raise ValueError("Stale or mismatched assessment receipt")
    a, _ = assess_packet(bundle, files, now)
    if receipt["allowed"] != a["allowed"] or assessment["evaluations"] != a["evaluations"]:
        raise ValueError("Assessment decision does not match frozen scoring")
    if not receipt["allowed"]:
        raise ValueError("Rejected v2/operational gate")


def verify_closeout(files, bundle=None):
    if bundle is not None:
        run = obj(files["run.json"])
        if sha(files["freeze.json"]) != bundle.freeze_sha or run["freeze_sha256"] != bundle.freeze_sha:
            raise ValueError("Closeout belongs to another freeze")
        if (instant(run["deadline_utc"]) - instant(run["started_utc"])).total_seconds() != 1800:
            raise ValueError("Closeout window changed")
        for entry in bundle.order:
            if sha(files[entry["request"]]) != bundle.request_hash(entry):
                raise ValueError("Closeout request changed")
    for name in ["server_exit.json", "watchdog_process_exit.json"]:
        if name not in files or obj(files[name]).get("confirmed_exited") is not True:
            raise ValueError("Final export lacks confirmed " + name)
    if "watchdog_exit.json" not in files or "cleanup_manifest.json" not in files:
        raise ValueError("Final export lacks watchdog/cleanup records")
    cleanup = obj(files["cleanup_manifest.json"])
    if cleanup.get("artifacts_preserved") is not True:
        raise ValueError("Artifact preservation unconfirmed")
    for name, info in cleanup.get("files", {}).items():
        if name not in files or sha(files[name]) != info["sha256"] or len(files[name]) != info["bytes"]:
            raise ValueError("Cleanup/export checksum mismatch: " + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["assess", "closeout"])
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = Bundle(HERE, (HERE / "freeze.json").read_bytes())
    files = read_archive(args.archive)
    if args.output.exists():
        raise ValueError("Output exists; preserve prior assessments")
    args.output.mkdir(parents=True)
    if args.command == "closeout":
        verify_closeout(files, bundle)
        (args.output / "closeout-verification.json").write_bytes(encoded({"verified": True,
            "archive_sha256": sha(args.archive.read_bytes()), "DESIGN": "pending", "linguistic_validation": "pending"}))
        print("Confirmed recorded exits/cleanup; live Windows state remains unverified.")
        return 0
    assessment, receipt = assess_packet(bundle, files, datetime.now(timezone.utc))
    (args.output / "assessment.json").write_bytes(encoded(assessment))
    (args.output / "receipt.json").write_bytes(encoded(receipt))
    with zipfile.ZipFile(args.output / ("return-" + receipt["checkpoint_id"] + ".zip"), "x", zipfile.ZIP_DEFLATED) as archive:
        archive.write(args.output / "assessment.json", "assessment.json")
        archive.write(args.output / "receipt.json", "receipt.pending.json")
    print(json.dumps({"checkpoint": receipt["checkpoint_id"], "allowed": receipt["allowed"],
        "v2_strict_passes": assessment["v2_strict_passes"], "v1_request_count": assessment["v1_request_count"],
        "receipt_sha256": sha(encoded(receipt)), "reason": receipt["reason"]}, indent=2))
    return 0 if receipt["allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

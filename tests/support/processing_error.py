from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

from app.application.comparisons import CompareRequest, digest
from tests.support.synthetic import EXAMPLE


class RetrievalFailureComparison:
    def __init__(self, comparisons: CompareRequest, control_file: Path):
        self.store = comparisons.store
        self._comparisons = comparisons
        self._control_file = control_file
        self._target_digest = None
        self._fault_consumed = False
        self._attempts = []
        self._enabled = True
        self._adapters = {name: getattr(comparisons, name)
            for name in ("interpreter", "knowledge", "renderer", "store", "clock")}

    def execute(self, submission):
        service = self._comparisons
        key_digest = digest(submission.key)
        if not self._enabled:
            return service.execute(submission)
        if self._target_digest is None:
            try:
                control = json.loads(self._control_file.read_text())
            except FileNotFoundError:
                return service.execute(submission)
            if (control.get("submission_key_digest") != key_digest or submission.text != EXAMPLE
                    or submission.search_location != {"country_code": "CH"}):
                return service.execute(submission)
            self._target_digest = key_digest
        if key_digest != self._target_digest:
            return service.execute(submission)

        counts = dict.fromkeys(("interpret", "retrieve", "assess_clock", "prepare", "prepare_coverage", "save"), 0)
        timeline = []
        attempt = {"counts": counts, "fault_raised": False, "returned_outcome": None, "timeline": timeline}

        def call(name, operation, *args):
            counts[name] += 1
            timeline.append(name + "_entered")
            result = operation(*args)
            timeline.append(name + "_returned")
            return result

        def retrieve(interpretation, effective_submission):
            counts["retrieve"] += 1
            timeline.append("retrieve_entered")
            if not self._fault_consumed:
                self._control_file.unlink(missing_ok=True)
                self._fault_consumed = True
                attempt["fault_raised"] = True
                timeline.extend(["matching_control_consumed", "retrieval_exception_after_interpretation"])
                raise RuntimeError("Synthetic test-only retrieval failure")
            result = service.knowledge.retrieve(interpretation, effective_submission)
            timeline.append("retrieve_returned")
            return result

        controlled = replace(service,
            interpreter=SimpleNamespace(interpret=lambda text: call("interpret", service.interpreter.interpret, text)),
            knowledge=SimpleNamespace(retrieve=retrieve),
            renderer=SimpleNamespace(
                prepare=lambda *args: call("prepare", service.renderer.prepare, *args),
                prepare_coverage=lambda *args: call("prepare_coverage", service.renderer.prepare_coverage, *args)),
            store=SimpleNamespace(find=service.store.find, save=lambda prepared: call("save", service.store.save, prepared)),
            clock=lambda: call("assess_clock", service.clock))
        try:
            result = controlled.execute(submission)
            attempt["returned_outcome"] = result["outcome"]
            return result
        finally:
            self._attempts.append(attempt)
            evidence = {"attempts": self._attempts,
                "total_counts": {name: sum(item["counts"][name] for item in self._attempts) for name in counts},
                "fault_consumed": self._fault_consumed,
                "original_adapters_unchanged": all(getattr(service, name) is adapter for name, adapter in self._adapters.items()),
                "raw_originating_proofs_or_requests_recorded": False}
            destination = self._control_file.with_suffix(".evidence.json")
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            temporary.write_text(json.dumps(evidence, indent=2) + "\n")
            temporary.replace(destination)

    def cleanup(self):
        self._enabled = False
        self._target_digest = None
        self._control_file.unlink(missing_ok=True)

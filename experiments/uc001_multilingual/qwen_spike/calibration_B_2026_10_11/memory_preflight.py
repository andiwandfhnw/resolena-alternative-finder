"""Record the same sample used by unchanged experimental preflight thresholds."""
import datetime
from pathlib import Path
import shutil


def cgroup_context():
    result = {}
    for name in ["memory.max", "memory.high", "memory.current", "memory.peak",
                 "memory.events", "memory.pressure"]:
        try:
            result[name] = (Path("/sys/fs/cgroup") / name).read_text().strip()
        except OSError:
            result[name] = None
    try:
        result["process_cgroup"] = Path("/proc/self/cgroup").read_text().strip()
    except OSError:
        result["process_cgroup"] = None
    result["scope"] = "Visible cgroup namespace only; hidden ancestors are not verified"
    return result


def enforce_preflight(available, config, scratch, write, *, disk_free=None,
                      timestamp=None, context=None):
    timestamp = timestamp or (lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    disk_free = disk_free or (lambda path: shutil.disk_usage(path).free)
    context = context or cgroup_context
    measured_at = timestamp()
    memory = available()
    disk = disk_free(scratch)
    memory_min = config["preflight_memory_min_bytes"]
    disk_min = config["scratch_budget_bytes"]
    failed = []
    if memory < memory_min:
        failed.append("memory")
    if disk < disk_min:
        failed.append("disk")
    row = {"utc": measured_at, "measured_available_bytes": memory,
           "minimum_available_bytes": memory_min, "measured_free_disk_bytes": disk,
           "minimum_free_disk_bytes": disk_min, "failed_guards": failed,
           "measurement_source": "/proc/meminfo MemAvailable; host/VM estimate, not cgroup headroom",
           "cgroup_context": context(), "thresholds_changed": False}
    write("preflight_guard.json", row)
    if failed:
        raise RuntimeError("Preflight RAM/disk guard: " + ", ".join(failed))
    return row

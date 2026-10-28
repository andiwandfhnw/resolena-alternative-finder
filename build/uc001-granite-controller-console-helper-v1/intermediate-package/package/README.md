# Console-helper correction — NOT AUTHORIZED / NOT EXECUTED

This separate package prepares the harmless ownership self-test to account for an
optional zero-or-one verified console helper beside the interpreter under each
applicable verified launcher. The interpreter remains the launcher's child; it
does not become the console helper's parent.

Helper acceptance requires a retained query-only PID/creation identity, the exact
verified launcher parent, creation no earlier than that launcher, the exact native
GetSystemDirectoryW-derived conhost.exe path (Windows case-insensitive full-path
comparison), stable revalidation, expected private-Job membership and no query errors.
Basenames, arbitrary conhost paths and other system executables are insufficient.
Multiple helpers, extra processes, missing interpreters, unavailable identities and
unknown membership still fail closed. Unknown/unclassified children are never directly terminated.

Accepted helper cleanup and revalidation must confirm identity-bound exits; no
helper is silently ignored during cleanup. Existing private-Job cleanup remains
unchanged; query-only handles add no authority to terminate unclassified children.
Outside helpers receive no direct termination: after launcher/interpreter cleanup,
their retained handle must yield a stable non-259 exit code before the 20-second
deadline. Owned helpers must also have matching identity-bound private-Job exit
evidence. A raw 259 outside the Job stays unresolved. Exact owned identities,
active count and lifetime total must equal the six base processes plus only the
admitted helpers; replacement helpers and transient lifetime extras fail.

Raw unknown_child_identity records collect metadata without granting roles;
console_helper_accepted/revalidated events record the separate role decision.
Toolhelp supplies no birth identity, so snapshot-to-open PID reuse remains a limit.
Outside scoped snapshots cannot exclude every unobserved transient process.

All previous Windows attempts are consumed and preserved. This package grants no
execution permission. A later explicit owner authorization is required before
using `Run-ConsoleHelperCheck.ps1 -OwnerAuthorized`. The switch records that later
approval; it does not obtain approval.

Use only a fresh `granite-controller-console-helper-v1` directory and the approved
separate Granite Python 3.12.11 environment. The runner verifies the externally
supplied manifest hash, exact package contents, helper hashes and inactive native
build template before one harmless ownership self-test. It prints and retains a
fresh sibling `ownership-console-helper-<GUID>` result/log directory.
On failure, preserve all output and stop without fixes or retry.

Offline checks establish preparation only, not Windows ownership, resource fit,
runtime compatibility, helper cleanup success or model suitability. No broad
process inventory is added. Source acquisition, configure/build, glslc, GPU probes,
model/server startup and inference remain unauthorized. Preserve original packages,
consumed attempts, frozen Granite settings, Python environments and all evidence.

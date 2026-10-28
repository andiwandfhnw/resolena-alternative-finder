# Granite compatibility result and native-tool discovery preparation — 2026-10-25

## Owner-executed compatibility evidence

The [verbatim supplied owner report](owner-compatibility-report.txt) records success
at **2026-10-25T17:10:05.928520+00:00**, reviewed by the advisor, not executed on
Windows by Codex. Its SHA-256 is
`d2893225bad8de035b11720ee7842a9446cb23d49bf49d50122847449a1b3841`.
This preserves the text supplied in the request; no desktop JSON or SQLite file
was read remotely or reconstructed as an independent raw export.

The report identifies check hash
`8a3bf0f118bb467d7e77c0108af1d7635c7210147de47e59e90ba81180777f7f`,
Python 3.12.11 in the separate Granite environment, transferred-worktree imports,
one POST and actual **201 / comparison / saved**. Request/option/link counts are
**0/0/0 → 1/2/2**; seeded alternatives/evidence remain **2/2**. Projection and option
snapshots match, client closed, one engine disposed, forbidden attempts empty;
no model startup/live assessment. Saved request:
`c236c561-7fa3-4acb-8ab3-660e186d7817`.

Owner retains the output at
`C:\Users\AndiWand\Downloads\granite-handoff-2026-10-25\build\test-only\granite-windows-compat-v1-dd960796-e5a1-41f4-bb85-c3b09c89ba86`.
The advisor checked consistency within the uploaded response, identities and
evidence-link lists, **not the desktop SQLite file directly**. Credit is limited
to this synthetic Windows application-dependency path. Granite suitability, native
runtime compatibility and live execution remain unverified. No setup, handoff or
compatibility check was repeated; the earlier preparation receipt remains historical.

## Executable read-only discovery

[discover.ps1](discover.ps1) is the complete standalone check, outside the freeze.
Size: **13471 bytes**. SHA-256:
**`40c18b7ede228ba9bfbc611d2365c1970245de3667d7394646a5d4d59753d1ba`**.

It identifies only Git, CMake, Ninja, x64 MSVC/Windows SDK and Vulkan SDK/compiler:

- Exact application names in current command resolution, standard Program Files
  Git/CMake locations and named GitForWindows product registry values.
- Existing standard-path `vswhere.exe` only: VS instances and x64 VC/CMake component
  queries. No utility is downloaded. Fallback inspects only direct numeric VS
  version directories and Community/Professional/Enterprise/BuildTools locations.
  MSVC inspection is limited to direct toolset versions and Hostx64/x64 payloads;
  bundled CMake/Ninja use their exact documented relative paths.
- Named Windows Kits `KitsRoot10` metadata in both registry views, its environment/
  standard roots and direct SDK version directories: selected x64 headers/libs/rc.
- Only process/user/machine `VULKAN_SDK`/`VK_SDK_PATH` roots and direct version
  directories under the standard VulkanSDK root: selected compiler/header/library
  and SPIRV-Headers config paths. Both `Lib` and `share` config locations are checked.

Output separates installation identification, current-shell resolution, bounded
non-discovery and unverified version/build compatibility. File/product/directory
version metadata is labelled; a directory version is not a verified servicing
version. Missing metadata stays unknown. Portable/custom locations outside these
checks can remain undiscovered; **not found does not establish machine-wide absence**.
Ninja has no assumed universal installer location.

The script writes no files, exports no registry/inventory, makes no network calls
and uses no recursive scan or old experiment-directory search. Only an already
installed vendor `vswhere` utility may execute; queries have a ten-second limit
and can terminate only that query's owned process on timeout. Tool versions are
read as file metadata: **no compiler, Git, CMake, Ninja, glslc or GPU utility runs**.
No environment activation, PATH/registry edits, installation, service or build.

The pinned source-build route remains **Windows x64/Vulkan**, llama.cpp commit
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. Its Vulkan CMake source requires CMake
at least 3.19, Vulkan/glslc and SPIRV-Headers CONFIG. Discovery reports related payload
presence only; it does not run configure, which contains shader-compilation probes.
Version/driver/backend/build compatibility is not established by this check.

## Windows PowerShell — owner desktop only

Download only discover.ps1 through the Codespaces Explorer to
`C:\Users\AndiWand\Downloads\granite-tool-discovery-v1.ps1`.
Run once in the existing **64-bit Windows PowerShell** session. Do not activate a
developer environment or change policy/PATH/registry for this check.

```powershell
$ErrorActionPreference = 'Stop'
$GraniteDiscovery = 'C:\Users\AndiWand\Downloads\granite-tool-discovery-v1.ps1'
if ((Get-FileHash -LiteralPath $GraniteDiscovery -Algorithm SHA256).Hash.ToLowerInvariant() -ne '40c18b7ede228ba9bfbc611d2365c1970245de3667d7394646a5d4d59753d1ba') { throw 'Discovery file hash differs: stop.' }
& $GraniteDiscovery
```

Return the JSON output, including notes/errors, for review. No desktop discovery
has been executed by this session. Missing-tool installation needs a separate,
concrete owner approval after that output; no installation/build follows now.

## Primary-source basis and preparation evidence

Sources consulted only for the bounded discovery method/pinned requirements:
[Microsoft vswhere VC discovery](https://github.com/microsoft/vswhere/wiki/Find-VC),
[Git installer metadata](https://github.com/git-for-windows/build-extra/blob/main/installer/install.iss),
[Microsoft CMake/Ninja locations](https://raw.githubusercontent.com/microsoft/vscode-cmake-tools/main/src/paths.ts),
[VS bundled CMake](https://raw.githubusercontent.com/microsoft/vscode-cmake-tools/main/src/vsInstanceCMake.ts),
[Microsoft Windows Kits lookup](https://github.com/microsoft/DirectXShaderCompiler/blob/main/cmake/modules/FindD3D12.cmake),
[LunarG SDK layout](https://vulkan.lunarg.com/doc/view/1.4.313.0/windows/getting_started.html),
[SPIRV-Headers config layout](https://raw.githubusercontent.com/KhronosGroup/SPIRV-Headers/main/CMakeLists.txt),
[pinned Vulkan build requirements](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/ggml/src/ggml-vulkan/CMakeLists.txt).
No binaries, runtime source tree or models were acquired.

Codespace verification used only the installed PowerShell parser's `ParseFile`
and static command-AST inspection, plus standard-library file hashes. Syntax
passed; **the script, registry queries, discovery utility and Windows checks were
not executed**. Static review corrected the second SPIRV-Headers config location.
Documentation links, artifact hashes, Markdown fences and new whitespace checks
passed. All 832 previously protected files outside TASKS and all 74 original
Granite preparation/handoff/proposal/check files retain their fingerprints
(overlapping counts are not added). Previous TASKS entries and Priority 5 history
are preserved. Read-only Git checks confirm unchanged HEAD, branch, index and
existing file-status entries. `git diff --check` exits 2 only for the preserved
historical TASKS trailing space at line 2503. Only TASKS and these new discovery/
receipt/report files were written. Both Python environments, freeze/archive and
application files remain unchanged; no desktop artifacts were read remotely.

PHASE: 3 / STATUS: in-progress; Priorities 3/4 partial; Priority 6/Phase 4 pending.
Priority 5 acceptance/ADR-007 and closed Qwen/experiments remain unchanged. Normal
app.main stays unconfigured; real drafts inactive; reference permissions unchanged.

# Windows shared-validator environment only

Owner-operated Windows PowerShell **5.1 x64**, normal user. No launcher/WindowsApps
discovery, model, transport, capture/replay runner or application changes.
Python **3.12.10 is the last official 3.12 Windows installer**, not the latest
security-patched 3.12 release ([release](https://www.python.org/downloads/release/python-31210/),
[subsequent security release](https://www.python.org/downloads/release/python-31215/)).
[Installer options](https://docs.python.org/3.12/using/windows.html#installing-without-ui).
Installation creates ordinary per-user Python registration and installer caches;
PATH, launcher, associations, shortcuts and unrelated installations are preserved.
No automatic restart, repair, source build, dependency upgrade or package fallback.
Explicit `-X utf8` preserves multilingual files with the unchanged Python readers;
it changes no Windows locale setting. pip configuration is disabled for these
commands only, then the prior process setting is restored.

## Transfer once, then set up

Download these four files through the existing Codespace Files view into
`C:\ResolenaExperiments\uc001-validator-setup` (no Git checkout or SSH):

- This `README.md`.
- [artifacts.json](artifacts.json): official URLs, exact sizes/hashes, dependency metadata and source hashes.
- [requirements-win-py312.txt](requirements-win-py312.txt): 11 adapter/domain dependencies plus pytest and its five dependencies.
- [shared-validation-source.zip](../../build/uc001-validator-setup/shared-validation-source.zip): **68,374 bytes**, SHA-256
  `c2ddf585e211325197802c7b9cea3af22252a6111035e6d84f53d1c26cfa871d`.

The small source ZIP contains 34 **unchanged** files, including the original
bundle files required by `load_bundle`'s integrity check and the matching v1.3.0
controls/schema/cases. It contains no model/runtime assets. Included legacy
launch/preflight files are hashed only; **do not run them**. No second validator.

Installer: **26,964,224 bytes**; 17 binary wheels: **4,937,934 bytes**;
total possible new external payload **31,902,158 bytes**. Installer SHA-256
`67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb`
comes from Python.org's HTTPS `.sigstore` message digest; cryptographic Sigstore
bundle/transparency verification was **not** performed. The command also requires
a valid Python Software Foundation Authenticode signature before installation.
Wheel URLs/sizes/SHA-256 come from each exact release's official PyPI JSON.
Actual downloaded bytes/hashes/signature remain Windows checks.
All 16 non-Windows-specific package versions match current Codespace metadata,
including httpx **0.28.1**, Pydantic **2.13.5** and pydantic-core **2.46.5**.
The additional pin is pytest's Windows-only **colorama 0.4.6**. No root requirement
or application dependency is changed.

The original **104,857,600-byte** cumulative allowance remains. Known acquisitions:
gh 18,317,085 + eight Debian archives 7,508,700 + one copy each of the original
two transport scripts 8,546, logging v1 6,616 and v2 6,535 = **25,847,482 bytes**.
Reserve **262,144 bytes** for this entire handoff. With no additional prior
acquisitions and no cache reuse, at most **46,845,816 bytes** remain afterward.
This is conditional accounting, not proof that other transfers did not happen.
At the prompt, enter reconciled additional prior acquisitions/re-downloads under
this allowance, including any previously acquired installer/wheels. Enter zero
only if confirmed; if unknown, **stop**. Retain the reservation even on failure.
No ledger/allowance reset; a previous reservation stops automatic repeat execution.

Place any already acquired exact artifacts in
`C:\ResolenaExperiments\tools\uc001-validator-cache` first; matching cached files
are reused, mismatches stop without replacement. New payload downloads occur
only on Windows, once per missing artifact, with no redirect or retry.

Paste this single setup block. It stops before downloads if either installation
target or a Python 3.12 registration already exists; that narrow installation
conflict guard does not repeat PATH/launcher discovery. Installer exit 3010 also
stops; any required restart/system-runtime prerequisite needs separate resolution.

```powershell
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not [Environment]::Is64BitProcess -or $PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { throw 'Use Windows PowerShell 5.1 x64' }
$Setup = 'C:\ResolenaExperiments\uc001-validator-setup'
$Target = 'C:\ResolenaExperiments\tools\python-3.12.10'
$Venv = 'C:\ResolenaExperiments\uc001-validator-env'
$Cache = 'C:\ResolenaExperiments\tools\uc001-validator-cache'
$Source = Join-Path $Setup 'source'
$Receipt = Join-Path $Setup 'download-reservation.json'
$M = Get-Content -LiteralPath (Join-Path $Setup 'artifacts.json') -Raw | ConvertFrom-Json
foreach ($p in @($Target,$Venv,$Source,$Receipt,'HKCU:\Software\Python\PythonCore\3.12','HKLM:\Software\Python\PythonCore\3.12')) {
    if (Test-Path -LiteralPath $p) { throw "Existing target/registration/reservation; stop without changing it: $p" }
}
[long]$Extra = 0
$Answer = Read-Host 'Reconciled additional prior acquisition bytes (unknown = stop; zero only if confirmed)'
if (-not [long]::TryParse($Answer,[ref]$Extra) -or $Extra -lt 0) { throw 'Prior accounting unresolved' }
if ($Extra -gt $M.download_cap_bytes) { throw 'Cumulative allowance exhausted' }
$HandoffBytes = (@('README.md','artifacts.json','requirements-win-py312.txt','shared-validation-source.zip') | ForEach-Object { (Get-Item -LiteralPath (Join-Path $Setup $_)).Length } | Measure-Object -Sum).Sum
if ($HandoffBytes -gt $M.handoff_transfer_reservation_bytes) { throw 'Handoff reservation exceeded' }
function Assert-Artifact($Path,$A) {
    if ((Get-Item -LiteralPath $Path).Length -ne $A.bytes -or (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $A.sha256) { throw "Size/hash mismatch; retain evidence and stop: $Path" }
}
$Zip = Join-Path $Setup $M.source_transfer.filename
Assert-Artifact $Zip $M.source_transfer
$All = @($M.installer) + @($M.wheels)
$Missing = @($All | Where-Object {
    $p = Join-Path $Cache $_.filename
    if (Test-Path -LiteralPath $p) { Assert-Artifact $p $_; $false } else { $true }
})
[long]$NewBytes = 0
foreach ($a in $Missing) { $NewBytes += $a.bytes }
[long]$Reserved = $M.known_prior_minimum_bytes + $Extra + $M.handoff_transfer_reservation_bytes + $NewBytes
if ($Reserved -gt $M.download_cap_bytes) { throw 'Cumulative allowance would be exceeded; stop' }
$R = [ordered]@{ outcome='reserved_not_installed'; manifest_sha256=(Get-FileHash -LiteralPath (Join-Path $Setup 'artifacts.json') -Algorithm SHA256).Hash.ToLowerInvariant(); requirements_sha256=(Get-FileHash -LiteralPath (Join-Path $Setup 'requirements-win-py312.txt') -Algorithm SHA256).Hash.ToLowerInvariant(); source_zip_sha256=$M.source_transfer.sha256; prior_basis='recorded archives plus one copy of four transport scripts'; known_prior_bytes=$M.known_prior_minimum_bytes; owner_reported_additional_prior_bytes=$Extra; handoff_reserved_bytes=$M.handoff_transfer_reservation_bytes; new_payload_reserved_bytes=$NewBytes; cumulative_reserved_bytes=$Reserved; remaining_bytes=($M.download_cap_bytes-$Reserved); reused=@($All | Where-Object { $_ -notin $Missing } | ForEach-Object { $_.filename }); newly_acquired=@(); error=$null }
$R | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Receipt -Encoding UTF8
$null = New-Item -ItemType Directory -Path $Cache -Force
$PriorTls = [Net.ServicePointManager]::SecurityProtocol
$PriorPipConfig = [Environment]::GetEnvironmentVariable('PIP_CONFIG_FILE','Process')
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
try {
    foreach ($a in $Missing) {
        $u = [uri]$a.url
        if ($u.Scheme -ne 'https' -or $u.Host -notin @('www.python.org','files.pythonhosted.org')) { throw 'Unexpected artifact origin' }
        $q = [Net.HttpWebRequest]::Create($u)
        $q.AllowAutoRedirect = $false; $q.Timeout = 30000; $q.ReadWriteTimeout = 30000
        $response = $null; $inputStream = $null; $outputStream = $null
        try {
            $response = $q.GetResponse()
            if ([int]$response.StatusCode -ne 200 -or $response.ContentLength -ne $a.bytes) { throw 'Unavailable/changed artifact; no substitute' }
            $inputStream = $response.GetResponseStream()
            $outputStream = [IO.File]::Open((Join-Path $Cache $a.filename),[IO.FileMode]::CreateNew)
            $buffer = New-Object byte[] 65536
            [long]$left = $a.bytes
            while ($left -gt 0) {
                $n = $inputStream.Read($buffer,0,[int][Math]::Min($buffer.Length,$left))
                if ($n -le 0) { throw 'Truncated download; no retry' }
                $outputStream.Write($buffer,0,$n); $left -= $n
            }
        } finally {
            if ($outputStream) { $outputStream.Dispose() }; if ($inputStream) { $inputStream.Dispose() }; if ($response) { $response.Dispose() }
        }
        Assert-Artifact (Join-Path $Cache $a.filename) $a
        $R.newly_acquired += $a.filename
        $R | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Receipt -Encoding UTF8
    }
    $Installer = Join-Path $Cache $M.installer.filename
    $Signature = Get-AuthenticodeSignature -LiteralPath $Installer
    if ($Signature.Status -ne 'Valid' -or $null -eq $Signature.SignerCertificate -or $Signature.SignerCertificate.GetNameInfo([Security.Cryptography.X509Certificates.X509NameType]::SimpleName,$false) -cne 'Python Software Foundation') { throw 'Valid PSF installer signature required' }
    $R.signature = 'Valid Python Software Foundation'
    $Arguments = @('/quiet','/norestart','/log',('"'+(Join-Path $Setup 'python-install.log')+'"'),'InstallAllUsers=0',('TargetDir="'+$Target+'"'),'PrependPath=0','AppendPath=0','Include_launcher=0','InstallLauncherAllUsers=0','AssociateFiles=0','Shortcuts=0','Include_exe=1','Include_lib=1','Include_pip=1','Include_doc=0','Include_test=0','Include_tcltk=0','Include_tools=0','Include_dev=0','Include_symbols=0','Include_debug=0','CompileAll=0')
    $Process = Start-Process -FilePath $Installer -ArgumentList $Arguments -Wait -PassThru
    $R.installer_exit_code = $Process.ExitCode
    if ($Process.ExitCode -ne 0) { throw "Installer stopped: exit $($Process.ExitCode); no automatic restart/repair" }
    & 'C:\ResolenaExperiments\tools\python-3.12.10\python.exe' -I -X utf8 -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' }
    $env:PIP_CONFIG_FILE = 'nul'
    & 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe' -I -X utf8 -m pip --isolated --disable-pip-version-check install --no-index --no-cache-dir --only-binary=:all: --require-hashes --find-links $Cache -r (Join-Path $Setup 'requirements-win-py312.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Pinned offline wheel installation failed; no fallback' }
    & 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe' -I -X utf8 -m pip --isolated --disable-pip-version-check check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency compatibility failed' }
    Expand-Archive -LiteralPath $Zip -DestinationPath $Source
    $R.outcome = 'setup_finished_compatibility_pending'
} catch { $R.outcome = 'stopped'; $R.error = $_.Exception.Message; throw }
finally {
    [Environment]::SetEnvironmentVariable('PIP_CONFIG_FILE',$PriorPipConfig,'Process')
    [Net.ServicePointManager]::SecurityProtocol = $PriorTls
    $R | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Receipt -Encoding UTF8
}
```

## Offline compatibility check

After successful setup, paste this block in the same window. All HTTP checks
use `httpx.MockTransport`; it makes **no connection**. The original tests are
selected explicitly to avoid importing the web/database fixture stack or running
legacy Windows preflights. The JSON schema comparison is exactly the existing
`json.loads(schema_file.read_text()) == WireResult.model_json_schema()` rule;
a mismatch fails, without regenerating or normalizing the frozen schema.

```powershell
$Out = Join-Path $Setup ('results\'+[guid]::NewGuid().ToString())
$null = New-Item -ItemType Directory -Path $Out
$Check = @'
import contextlib, hashlib, importlib.metadata as metadata, json, os, platform, struct, sys
from pathlib import Path
root, manifest_path, out = map(Path, sys.argv[1:])
m = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
r = {'outcome': 'compatibility_failed', 'scope': 'environment and synthetic offline checks only', 'qualified_linguistic_review': 'pending', 'model_readiness_verified': False, 'windows_runtime_gpu_verified': False}
try:
    assert sys.platform == 'win32' and platform.python_implementation() == 'CPython'
    assert sys.version_info[:3] == (3, 12, 10) and struct.calcsize('P') == 8 and platform.machine().lower() == 'amd64'
    assert sys.flags.utf8_mode == 1
    assert Path(sys.prefix) == Path(r'C:\ResolenaExperiments\uc001-validator-env')
    assert Path(sys.base_prefix) == Path(r'C:\ResolenaExperiments\tools\python-3.12.10')
    r['python'] = sys.version; r['architecture'] = platform.machine()
    r['executable'] = sys.executable; r['venv'] = sys.prefix; r['base_python'] = sys.base_prefix
    r['dependencies'] = {a['name']: metadata.version(a['name']) for a in m['wheels']}
    r['installer_bundled_pip'] = metadata.version('pip')
    assert all(r['dependencies'][a['name']] == a['version'] for a in m['wheels'])
    for name, expected in m['source_transfer']['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == expected, name
    sys.path[:0] = [str(root/'src'), str(root)]
    from app.infrastructure.llama_cpp_interpreter import WireResult, decode_result
    from app.domain.interpretation import ContractViolation, LanguageOutcome, apply_language_policy
    from scripts.uc001_execution_v1_3_0.controls import check_case_state
    b = root/'scripts/uc001_execution_v1_3_0'
    f = json.loads((b/'freeze.json').read_text())
    for name in ('controls.py', 'schema.json', 'cases.json'):
        assert hashlib.sha256((b/name).read_bytes()).hexdigest() == f['files'][name]
    assert json.loads((b/'schema.json').read_text()) == WireResult.model_json_schema()
    r['frozen_schema_equal'] = True
    # Synthetic packet only: no interpreter/language-understanding evidence.
    packet = {'recognition': {'status': 'unknown', 'language': None}, 'meaning_status': 'needs_clarification', 'clauses': [{'span': {'quote': 'Velo', 'occurrence': 1}, 'meaning_status': 'needs_clarification', 'normalized': None, 'item_ids': []}], 'items': [], 'message': 'Synthetic environment check; clarify meaning.'}
    result = decode_result('Velo', json.dumps(packet))
    check_case_state(json.loads((b/'cases.json').read_text())['cases'][8], packet)
    try: apply_language_policy(result, {})
    except LanguageOutcome as e: assert e.code == 'meaning_uncertain'
    else: raise AssertionError('Clarification route did not stop')
    try: decode_result('Velo', '{}')
    except ContractViolation: pass
    else: raise AssertionError('Invalid contract accepted')
    os.chdir(root); os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    import pytest
    names = ['test_current_settings_must_be_verified_not_merely_requested', 'test_frozen_manifest_reconciles_meaning_uncertainty_before_language_preference', 'test_machine_state_gate_is_not_semantic_approval', 'test_protected_endpoint_authentication_proof_does_not_use_public_health', 'test_qualified_review_gate_rejects_unapproved_machine_expectations', 'test_schema_configuration_and_source_are_frozen']
    with (out/'pytest.txt').open('x', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        code = pytest.main(['-q', '-p', 'no:cacheprovider', '--basetemp', str(out/'pytest-tmp')] + ['tests/unit/test_contract_run_controls.py::'+name for name in names])
    r['pytest_exit_code'] = int(code)
    assert code == 0, 'Existing offline checks failed; retain pytest.txt'
    r['outcome'] = 'windows_validator_environment_compatible'
finally:
    (out/'compatibility.json').write_text(json.dumps(r, indent=2)+'\n', encoding='utf-8')
'@
& 'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe' -I -X utf8 -B -c $Check $Source (Join-Path $Setup 'artifacts.json') $Out
if ($LASTEXITCODE -ne 0) { throw "Compatibility failed; retain $Out" }
Get-Content -LiteralPath (Join-Path $Out 'compatibility.json') -Raw
```

Expected: `windows_validator_environment_compatible`, exact versions, schema equal,
and **7 existing tests passed** in `pytest.txt`. Keep `download-reservation.json`,
installer logs and the fresh result directory. On any failure, stop and preserve
partial files/receipts; no automatic second attempt.

Codespace evidence is [verification.json](../../build/uc001-validator-setup/verification.json).
Windows installation/signature/pip/schema/tests remain owner-run and unverified.
This checks neither real semantic correctness nor model/GPU readiness. Qualified
DE/FR/IT/EN review and the three live API/real-adapter checks remain pending;
no startup/generation allowance, model ledger, accepted requirement or phase changes.
Priority 3 partial; Phase 3 DEVELOP in-progress. Stop after this environment check.

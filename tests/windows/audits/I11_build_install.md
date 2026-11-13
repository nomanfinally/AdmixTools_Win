# I11: automated Windows source build and installation

Status: **functional checks recorded; independent hard audit pending**,
13 November 2026. This is a batch/PowerShell source-build helper, not an MSI
release or a full-suite numerical certification.

`build-install-windows.bat` forwards arguments to its adjacent PowerShell helper
using 64-bit Windows PowerShell. The default is `%ProgramFiles%\AdmixTools`
and Machine PATH; that mode refuses non-administrator execution before mutation.
`-CheckOnly` is read-only. `-NoInstallDependencies` blocks WinGet/pacman changes;
private pinned argp/Python build preparation still requires network access.

The helper checks Git, native x64 Python with venv/pip, MSYS2 and UCRT64 GCC,
binutils, GSL, OpenBLAS and zlib. Missing prerequisites can be installed using
WinGet, with full MSYS2 updates before missing library installation. It uses the
existing preparation and compiler flags; scientific code is unchanged.

Builds run in a new sibling staging directory under the selected installation
parent. Only selected tracked source/docs are copied, including current edits;
private guides, raw data and ignored caches are excluded. The copied tree does
not include `.git`. An explicit source revision and dirty-state flag are passed
to `build-windows.ps1`/`src/build_windows.py`, whose actual source/DLL hash records
remain part of build metadata. This provenance option changes no calculations.

All native payloads, adjacent DLLs/licenses and copied source/validation records
are promoted together after checks. A recognized previous installation is renamed
to a retained backup. Unrelated existing directories, junction destinations or
redirected ancestors are refused. Moves are constrained to the explicit sibling
paths and have bounded retries for transient file handles. No recursive deletion
is performed. Failure after promotion attempts to restore the earlier installation
and application PATH change; failures during rollback retain both the original
error and recovery locations. Prerequisite installations/upgrades are not undone.

PATH updates preserve other entries, remove only equivalent duplicates for the
selected bin folder, re-read the current value immediately before writing, and
broadcast an environment change. User/Machine/None scopes are explicit; updates
must keep the existing scope. Other already-running terminals can need restarting.

## Recorded checks

- Windows PowerShell 5.1 parses all setup scripts and the public guide examples.
- Read-only discovery succeeds with existing UCRT64 dependencies. Missing package
  and non-elevated default-install cases return failure before installation.
- A real fresh source build/install in an ignored directory containing spaces
  prepares argp, compiles 37 tools, verifies DLL hashes, passes all 35 expected
  integration statuses and the binary genotype round trip, and launches qpAdm.
- Its regression output matches the retained pinned pristine Linux fixture:
  **70 streams and 18 generated files exact**, after the existing narrow
  platform-metadata normalization. No floating-point tolerance is used.
- The batch entry point works when its own directory contains spaces and `&`.
- `test_build_install.ps1` reuses that verified payload and injects child-command
  outcomes to exercise preparation failure, post-promotion failure/rollback,
  successful update/backup, correct scalar validation-count metadata and refusal
  to overwrite an unrelated directory. It checks sentinel/record preservation
  and verifies persistent User/Machine PATH values did not change.
- PATH transformation checks cover empty values, case/trailing-slash duplicates
  and retention of unrelated entries without writing persistent environment data.

The full fresh build precedes final glue changes to diagnostic presentation,
source-provenance bookkeeping, destination checks, retry/rollback reporting and
installation metadata counting. Final boundary checks exercise the updated
promotion code using the compiled payload; they are not another compiler run.
Raw logs/results are local under `.private/build-install-tests/` and setup
transcripts under `%TEMP%`; neither should be published without redaction.

## Reproduction and limits

```powershell
.\build-install-windows.bat -CheckOnly -Msys2Root 'C:\msys64'
.\build-install-windows.bat -InstallRoot "$env:LOCALAPPDATA\Programs\AdmixTools-test" -Msys2Root 'C:\msys64' -PathScope None -NoInstallDependencies
```

After a successful local test installation, exercise injected failures with a
new ignored test directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/windows/test_build_install.ps1 -BuiltInstallRoot "$env:LOCALAPPDATA\Programs\AdmixTools-test" -Msys2Root 'C:\msys64' -TestOutput '.private\setup-boundaries-new'
```

The current test session is not elevated. Actual Program Files writes, persistent
Machine/User PATH writes/broadcast behavior, first-time WinGet dependency installs,
MSYS2 core-update/restart handling and every administrator-account configuration
have not been executed. Installer lifecycle/repair is not implemented; MSI remains
deferred. The inherited blocked qpfmvmix target remains blocked. No upstream bug
corrections, algorithms or optimization settings are introduced by this helper.

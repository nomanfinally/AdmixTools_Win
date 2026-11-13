# ADMIXTOOLS on Windows

This is the **public, generalized guide**. Paths use variables or example
locations; replace them with your own settings. To generate a parallel guide
containing this checkout's actual paths, run from the repository in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\New-PersonalWindowsGuide.ps1 -Msys2Root 'C:\msys64'
```

Use your MSYS2 installation root for `-Msys2Root`. The command creates
`README.WINDOWS.personal.md`, which is ignored by Git. Regenerate it after changes
to this public guide. Do not force-add it or private recovery files to Git.

This guide takes a new Windows installation from prerequisites to a compiled
suite, a first PowerShell analysis, PATH configuration and verification.
Documentation checked on **14 November 2026** against this checkout's scripts.
The recorded development environment uses x64 Windows 11, Windows PowerShell
5.1, Python 3.13 and MSYS2 UCRT64; PowerShell 7 can also invoke the scripts.
A fresh installation on every supported Windows version has not been retested.

## Choose your starting point

| Your situation | Start here |
| --- | --- |
| Have the standalone MSI; want to run analyses | [Standalone installer](#standalone-installer) |
| New computer, no compiler installed | [1. Prerequisites](#1-prerequisites) |
| Dependencies installed, source not downloaded | [2. Obtain the source](#2-obtain-the-source-and-choose-a-branch) |
| Existing checkout, ready to build | [3. Prepare GNU argument parsing](#3-prepare-gnu-argument-parsing), then [4. Compile](#4-compile-the-suite) |
| Want an automated Program Files build/install | [Automated batch build and installation](#automated-batch-build-and-installation) |
| Complete built suite already available | [5. Run from PowerShell](#5-run-from-powershell) |
| Want commands available from any folder | [6. Configure PATH](#6-add-the-suite-to-your-user-path) |
| Want to check the installation | [7. Verify](#7-verify-the-build) |
| An installation or command fails | [8. Troubleshooting](#8-troubleshooting) |
| Updating, moving or uninstalling | [9. Updates and removal](#9-updates-and-removal) |

Use the terminal named above each command block:

| Terminal | What runs there |
| --- | --- |
| **MSYS2 UCRT64**, from the Start menu | `pacman` dependency installation and updates |
| **Windows PowerShell 5.1 / PowerShell 7** | Git checkout, preparation/build scripts, analyses and PATH setup |
| **WSL/Linux**, optional | The pristine Linux reference and comparison runs |

Do not type the Markdown fences or shell prompt characters. Run the sections
in order; variables such as `$Repo` and `$Msys2Root` belong to the current
PowerShell session. Reassign them after opening a new terminal.

Current scope: Windows porting and presentation only. Earlier upstream bug
repairs have been removed from active code and binaries. Calculations, sampling,
defaults, parameter acceptance and version behavior follow the unmodified pinned
Linux version, including inherited defects. See the
[restoration report](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md).

Windows-specific support retained: native helper processes, binary I/O and
64-bit offsets, UTF-8/long-path manifest, quoted parameter paths, UTF-8 BOM and
CRLF parameters, native temporary paths and owned-file cleanup. Continue saving
parameter files as UTF-8; UTF-16 is not a supported parameter format.

`-v` retains upstream behavior and may continue executing; use `-h` for documented
options. Inactive legacy parameters retain Linux behavior. In particular,
`output:`/`outputname:` can open or truncate a file without writing results;
omit them and save stdout with PowerShell redirection or `Tee-Object`.
No `maxreject` option or automatic rejection-sampling cap is implemented.

This is a native 64-bit Windows compatibility port of
[DReichLab/AdmixTools](https://github.com/DReichLab/AdmixTools), keeping the
upstream source layout, separate program names and numerical algorithms.
The first goal is matching Linux results and terminal output. Optimizations
remain deferred. A development MSI can now be built using the packaging scripts.

**Development status:** 37 executables build; 35 integration cases across 26
tools have been compared with a pinned Linux reference. Full-suite parity has
not yet been established. See [WINDOWS_PORT_STATUS.md](WINDOWS_PORT_STATUS.md)
for exact coverage and remaining work. Development is published on the
[`main` branch](https://github.com/nomanfinally/AdmixTools_Win/tree/main).
The per-tool hard compatibility audit is still pending; this is a development
source publication. Building an installer does not certify full-suite parity;
no installer is published to GitHub Releases by the build command.

For the sequential per-tool/module bug and compatibility review, see
[COMPATIBILITY_AUDIT.md](COMPATIBILITY_AUDIT.md). Existing fixture coverage does
not count as a completed hard audit.

## Standalone installer

Download the MSI from [GitHub Releases](https://github.com/nomanfinally/AdmixTools_Win/releases).
The first package is a development pre-release, not a full-suite parity certification.
Use `AdmixTools-<version>-windows-x64.msi` from the release's **Assets** section.
The MSI
contains its payload in one file: no companion ZIP, compiler, MSYS2, Python, WSL
or internet connection is required on the destination computer. It targets x64
Windows 10 version 1903 or later and Windows 11. ARM64 and 32-bit Windows have
not been validated.

1. Double-click the MSI and read the license and development-build notice.
2. Choose an installation directory writable by your account. The default is
   `%LOCALAPPDATA%\Programs\AdmixTools`. Installation is for the current user.
3. Select **Add AdmixTools to my user PATH** to run commands from any folder.
   Existing PATH entries are preserved; machine PATH is not changed.
4. Complete installation, then open a new PowerShell window. Restart VS Code
   if its terminals still have the previous PATH. Run:

   ```powershell
   Get-Command qpAdm -All
   qpAdm -h
   ```

If you leave PATH unchecked, run the executable by its full path:

```powershell
$InstallDir = Join-Path $env:LOCALAPPDATA 'Programs\AdmixTools'
& (Join-Path $InstallDir 'bin\qpAdm.exe') -h
```

The package includes the **37 currently supported native executables**, runtime
DLLs, Graphviz and Ghostscript for native graph rendering, documentation and
license notices. It excludes interpreter-based Perl/R/Python workflows and the
blocked legacy `qpfmvmix` target; those are not claimed as working offline tools.
Keep installed DLLs beside the executables. Keep datasets and results in a
separate analysis folder; use [the PowerShell examples](#5-run-from-powershell).

This development package is unsigned. Windows may show an unknown-publisher
warning; verify its source and SHA256 checksum before installing. For example:

```powershell
Get-FileHash -LiteralPath '.\AdmixTools-8.1.0-windows-x64.msi' -Algorithm SHA256
```

Compare the result with the maintainer's `.sha256` file. Checksums distributed
alongside an installer detect corruption; they do not replace a trusted source.

Close running tools before maintenance. Reopen the MSI for repair/removal, or
use Windows Settings **Apps > Installed apps > AdmixTools Windows > Uninstall**.
Uninstall removes installer-managed files and its PATH entry, preserving other
PATH entries and user-created files. Installation never forces a system restart.
For a newer MSI, keep the same account and installation folder; the package
supports major upgrades and blocks version downgrades. Use a higher numeric
package version for every distributed build; this is separate from each tool's
upstream `.w` executable version.

To build the MSI yourself, follow [packaging/windows/README.md](packaging/windows/README.md).
The portable ZIP beside it contains the same native payload, without installer
registration or automatic PATH integration. Distribution testing and limitations
are recorded in that packaging guide.

## Automated batch build and installation

`build-install-windows.bat` automates a **local source build and manual
installation**. It is not an MSI and does not create a Windows uninstall entry.
Use a Git checkout of this repository first (a source ZIP without `.git` does
not provide the revision required by this helper); the batch file and its adjacent
`build-install-windows.ps1` helper must be kept together.

For the default installation, right-click **`build-install-windows.bat` → Run as
administrator**. A plain double-click without administrator access stops with
instructions before making Program Files or machine PATH changes. The default
destination is `%ProgramFiles%\AdmixTools`, with commands under its `bin` folder.
The batch window stays open at the end when no arguments were supplied.

The batch/helper flow:

1. Checks x64 Windows, Git, native x64 Python with venv/pip, and the matching
   MSYS2 UCRT64 GCC, binutils, GSL, OpenBLAS and zlib packages.
2. Installs missing Git/Python/MSYS2 using
   [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/install)
   when available. Missing UCRT64 packages trigger the MSYS2-supported full
   upgrade in separate shell sessions, then package installation. This needs
   internet access and can also update other packages in that MSYS2 installation.
   See [MSYS2 automation](https://www.msys2.org/docs/ci/). Existing sufficient
   prerequisites are reused without an automatic global upgrade.
3. Copies tracked source files, including their current local edits, into a new
   build area **under the chosen installation parent**. With the default, builds
   run inside Program Files. The original checkout is not moved or modified.
   Private guides, `.private`, raw user data and existing build caches are not
   copied. The copied source retains upstream's `src`/`perlsrc` layout.
4. Prepares pinned GNU argp, compiles all 37 supported native executables, verifies
   runtime DLL hashes, and runs the 35-case synthetic integration suite. Its
   expected error case and binary genotype round trip are checked explicitly.
5. Installs the completed `bin` payload, licenses, source snapshot, provenance
   record and synthetic-check evidence. It adds **only the final `bin` folder**
   to machine PATH, preserving other entries and avoiding matching duplicates.

Open a new PowerShell window afterwards, then run `Get-Command qpAdm -All` and
`qpAdm -h`. Restart VS Code if its terminals still inherit the old PATH. Individual
tools keep upstream option behavior, including version switches that continue.

For an existing MSYS2 installation at another location, use an **administrator
PowerShell** from the repository directory:

```powershell
.\build-install-windows.bat -Msys2Root 'D:\msys64'
```

The helper checks `MSYS2_ROOT`, the default `C:\msys64`, the per-user
`%LOCALAPPDATA%\AdmixTools-build\msys64` cache, and an existing UCRT64 compiler
on PATH; pass `-Msys2Root` explicitly for other locations. MSYS2's compiler
installation is separate from the AdmixTools installation and normally stays at
its own existing root. Keep that root short and without spaces; the AdmixTools
destination itself can contain spaces.

Useful options, also accepted through the batch launcher:

```powershell
# Read-only prerequisite check; does not install packages or change PATH.
.\build-install-windows.bat -CheckOnly -Msys2Root 'C:\msys64'

# Require preinstalled system/toolchain prerequisites (private argp preparation
# still uses the network to obtain its pinned source and Python build tools).
.\build-install-windows.bat -Msys2Root 'C:\msys64' -NoInstallDependencies

# Custom installation folder. Machine PATH still requires administrator access.
.\build-install-windows.bat -InstallRoot 'D:\Applications\AdmixTools' -Msys2Root 'C:\msys64'

# Local-only build/install, without writing persistent PATH; useful for testing.
.\build-install-windows.bat -InstallRoot "$env:LOCALAPPDATA\Programs\AdmixTools" -Msys2Root 'C:\msys64' -PathScope None -NoInstallDependencies
```

`-PathScope User` adds the commands to the current Windows user's PATH instead.
A destination inside Program Files still needs administrator access. Keep the
same PATH scope when updating an existing installation. If elevation uses a
different administrator account, a User PATH change belongs to that account;
the default Machine scope applies to the computer.

Run the batch file again to rebuild/update. Only a destination containing its
recognized `admixtools-install.json` record is replaced; an unrelated existing
directory is refused. Successful updates retain the previous whole installation
in a neighboring `.backup-...` folder. Build failures preserve the previous tools
and do not add an AdmixTools PATH entry. Newly installed/upgraded prerequisites
are not uninstalled on a later build failure. If final promotion/PATH/smoke verification fails, the helper
attempts rollback and retains the failed build for diagnosis. Close running tools
before updating; file locks can prevent renaming an installation.

Local build transcripts are written to `%TEMP%\AdmixTools-build-install-*.log`.
They contain local machine details: do not commit them or post them publicly
without redaction. Keep analysis data outside the installation folder; both
Program Files and its copied source/build area are administrator-managed.
This script is not a repair/uninstall service. To remove it manually, first
remove its exact `bin` entry from the selected PATH scope, then remove only its
installation/backup folders when no tools are running. Preserve needed analysis
data and provenance. For registered repair and uninstall, use the separate
[standalone MSI](#standalone-installer) instead of this source-build helper.

Functional build checks do not certify full-suite numerical parity with pristine
Linux. The source build uses the same scientific code and build flags; no new
statistical behavior or optimization is introduced by this automation.

Recorded automation checks: a complete build/install into a new local folder
with spaces, 37 executable outputs, all 35 synthetic cases, 70 streams/18 files
matching the retained pristine-Linux regression, successful upgrade/backup and
injected failure/rollback checks. Batch invocation with spaces/`&` in its own path
and missing-prerequisite failures were checked. The test session was not elevated:
an actual Program Files write, machine PATH update and fresh WinGet/MSYS2 package
installation were not performed. Those administrator/bootstrap paths remain
explicit deployment checks. No persistent PATH values changed during validation.

## 1. Prerequisites

### What you need to build, and what you need to run

| Component | Build the suite | Run an already built native tool |
| --- | --- | --- |
| x64 Windows and PowerShell | Required | Required |
| Git for Windows | Required by preparation/source checkout | Not required |
| Native Windows Python 3.10 or later, with `venv`/pip | Required | Only for Python helpers and validation |
| MSYS2 UCRT64 GCC, binutils, GSL, OpenBLAS, zlib | Required | MSYS2 itself is not required; copied runtime DLLs are |
| GNU argp | Prepared automatically in section 3 | Statically linked into the relevant tools |
| Graphviz/Ghostscript | Optional | Only for the optional graph-rendering workflow |
| Perl/R or other helper dependencies | Optional | Only for the corresponding interpreter scripts |

Use 64-bit Windows 10 version 1903 or later, or Windows 11, PowerShell,
Git for Windows and Python 3.10 or later. The process manifest enables UTF-8
paths; long-path support also depends on Windows policy. Windows 11 and
PowerShell 5.1 were used for the recorded checks.
The build produces **x86-64** executables. Native ARM64 and 32-bit Windows builds
are not covered by this tutorial. Required RAM and temporary disk space depend
on your dataset and analysis; `.gz` inputs also require space for their expanded
contents. Keep analysis data outside the source checkout.

Install [Git for Windows](https://git-scm.com/install/windows) with its command-line
tools available to PowerShell. Install a normal native Windows Python from the
[official Windows downloads](https://www.python.org/downloads/windows/); Python
3.13 is the tested series. If using its traditional installer, enable its PATH
option. With another installation method, ensure the resulting `python` command
actually launches an interpreter. The embeddable Python ZIP is not the intended
build environment because preparation needs `venv` and pip.

Open a **new PowerShell window** after installing them and check:

```powershell
git --version
python --version
python -m pip --version
python -c "import sys, struct, venv; print(sys.executable); print('Python bits:', struct.calcsize('P') * 8)"
Get-Command git, python -All
$PSVersionTable.PSVersion
```

Use a 64-bit native Windows Python; its executable should be a Windows path.
If `python` opens a Store page or is not found, fix its installation/PATH or App
execution alias before continuing. `py` working alone is insufficient: the
repository scripts invoke **`python`**. You do not need Visual Studio, CMake,
Linux `make`, WSL, Git Bash or a global Meson/Ninja installation for this build.

### Install the matching MSYS2 libraries

Install [MSYS2](https://www.msys2.org/) following its
[official installer instructions](https://www.msys2.org/docs/installer/).
The examples below assume `C:\msys64`; a custom location also works. Open the
**MSYS2 UCRT64** terminal and update it:

```bash
pacman -Syu
```

If the updater closes the terminal or asks you to restart it, reopen UCRT64 and
run that command again until the full update completes. MSYS2 supports
[full system upgrades](https://www.msys2.org/docs/updating/); avoid updating one
library in isolation with a partially updated package database. Install:

```bash
pacman -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-binutils mingw-w64-ucrt-x86_64-gsl mingw-w64-ucrt-x86_64-openblas mingw-w64-ucrt-x86_64-zlib
echo "$MSYSTEM"
which gcc
gcc -dumpmachine
```

The last three commands should show `UCRT64`, `/ucrt64/bin/gcc`, and
`x86_64-w64-mingw32`. [UCRT64](https://www.msys2.org/docs/environments/) is the
environment used by this repository. The
[binutils package](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-binutils)
provides tools including `ar`, `objdump` and `windres`; the build uses `windres`
to embed the Windows application manifest.

Use the UCRT64 packages together. Do not substitute the MSYS `/usr/bin/gcc`
compiler or mix MINGW64/CLANG64 libraries with UCRT64. The build runs from
PowerShell; MSYS2 supplies the compiler and libraries. The resulting programs
run without an MSYS shell or WSL.

Return to **PowerShell** and set your MSYS2 root, not its `ucrt64\bin` subfolder:

```powershell
$Msys2Root = 'C:\msys64'  # Change this if you chose another installation folder.
foreach ($Name in 'gcc.exe', 'ar.exe', 'objdump.exe', 'windres.exe') {
    $ToolPath = Join-Path $Msys2Root "ucrt64\bin\$Name"
    if (-not (Test-Path -LiteralPath $ToolPath -PathType Leaf)) {
        throw "Required UCRT64 tool not found: $ToolPath"
    }
}
& (Join-Path $Msys2Root 'ucrt64\bin\gcc.exe') --version
```

The build scripts temporarily add the compiler folder to their process PATH and
restore it afterwards. You do not need to add MSYS2's `usr\bin` or the compiler
folder permanently to your user/system PATH to build or run native analyses.

## 2. Obtain the source and choose a branch

### Fresh checkout

```powershell
$Repo = Join-Path $env:USERPROFILE 'source\AdmixTools_Win'
New-Item -ItemType Directory -Path (Split-Path -Parent $Repo) -Force | Out-Null
git clone --branch main https://github.com/nomanfinally/AdmixTools_Win.git $Repo
if ($LASTEXITCODE -ne 0) { throw 'Clone failed; read the Git error above.' }
Set-Location -LiteralPath $Repo
git branch --show-current
git remote -v
```

The destination must not already contain another checkout. A short local path
is convenient; the repository does not need to be installed under `Program Files`
or run as Administrator. The `$Repo` example above expands to your own Windows
profile. Keep this variable for the later commands.

### Existing checkout

Use its actual location instead of cloning again:

```powershell
$Repo = Join-Path $env:USERPROFILE 'source\AdmixTools_Win'  # Or your checkout.
Set-Location -LiteralPath $Repo
git status --short
git branch --show-current
```

Preserve existing work before switching branches. If the tree is clean and you
intend to use the maintained port branch, `git switch main` selects it.
A topic branch may contain local work that is not on the published branch; this
guide does not automatically switch, reset or overwrite it.

Use `main` for the maintained port; it is this fork's default branch and the
place to commit ongoing porting work. Keep `master` as the separate upstream
tracking line. Optional topic branches can start from `main` for individual fixes.
The configured remotes are:

```text
origin    https://github.com/nomanfinally/AdmixTools_Win.git
upstream  https://github.com/DReichLab/AdmixTools.git
```

The port branch contains the narrow filename renames needed for a Windows
checkout. The original upstream revision contains 11 names with colons, which
ordinary Windows checkouts cannot create. The mapping is listed below; the
upstream directory layout is retained. `master` remains the upstream tracking
line; `main` contains the Windows-compatible checkout and is the default when
cloning or browsing this fork.

The former `windows-port` branch was renamed to `main` with its commit history
preserved. In an older clean clone that still uses that branch, migrate with:

```powershell
git fetch origin --prune
git branch -m windows-port main
git branch --set-upstream-to=origin/main main
git switch main
git pull --ff-only
git remote set-head origin -a
```

Use these commands only if the local `windows-port` branch exists and `main`
does not. Preserve local edits first. If that branch contains unpushed commits,
review them before any push; a fast-forward refusal is a reason to investigate,
not to reset or force-push. Clones predating the privacy-history cleanup should
be replaced with a fresh clone as described in [PRIVACY.md](PRIVACY.md).

## 3. Prepare GNU argument parsing

From the repository root in PowerShell:

```powershell
Set-Location -LiteralPath $Repo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\prepare-windows.ps1 -Msys2Root $Msys2Root
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed; resolve its error before building.' }
```

This invocation also works when your current terminal is PowerShell 7; it starts
Windows PowerShell for the script. `-ExecutionPolicy Bypass` applies to that
process. It does not permanently weaken the user or machine execution policy.
Managed computers may enforce policy separately; use the organization's permitted
method if the script remains blocked.

This creates a local Python environment under `src/.windows/`, installs pinned
Meson/Ninja build tools, fetches a pinned GNU argp source revision, builds it and
runs its included tests. This is needed by `transpose` and `merge_transpose` to
retain GNU command-line parsing and help. It does not change the system Python,
user PATH, or persistent PowerShell execution policy.

The preparation step needs internet access. Build dependencies and objects under
`src/.windows/` are generated and ignored by Git. See the pinned revision and
small diagnostic compatibility adjustment in `prepare-windows.ps1`.

Expected generated files include `src\.windows\venv\Scripts\python.exe` and
`src\.windows\argp\lib\libargp.a`. Do not activate this private Python
environment to run the native tools. A successful repeat preparation reuses the
pinned checkout and reconfigures its build. A reported unexpected argp revision
needs investigation; do not replace the pin with a random newer source.

## 4. Compile the suite

```powershell
Set-Location -LiteralPath $Repo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-windows.ps1 -Msys2Root $Msys2Root
if ($LASTEXITCODE -ne 0) { throw 'Build failed; read the compiler/linker output above.' }
```

For a different MSYS2 installation, pass its root directory, for example
`-Msys2Root C:\msys64`.
List the inventory without compiling:

```powershell
python src/build_windows.py --list
```

The equivalent PowerShell inventory command is
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build-windows.ps1 -ListTools`.
It does not require an installed compiler. The build should finish with a
`Built 37 executables ...` line for the full supported target list.

All 28 upstream default executables and 9 additional buildable targets are
installed in `bin/`. `qpfmvmix` is listed as blocked because its upstream source
is malformed. It is never silently replaced with a different implementation.

The build copies the required native DLLs into `bin/`. Keep these DLLs beside
the executables. It also copies upstream Perl/R/Python helpers into their usual
installed locations. Those scripts still need their respective interpreters;
they are not native executable conversions. `bin/windows-build.json` records
the baseline, compiler, flags, source hashes and runtime DLL hashes.

Inspect your actual build rather than assuming it used another machine's versions:

```powershell
$AdmixBin = (Resolve-Path -LiteralPath (Join-Path $Repo 'bin')).Path
$BuildInfo = Get-Content -LiteralPath (Join-Path $AdmixBin 'windows-build.json') -Raw | ConvertFrom-Json
$BuildInfo.compiler
$BuildInfo.upstream_commit
$BuildInfo.executables.Count
Get-ChildItem -LiteralPath $AdmixBin -Filter '*.exe' | Select-Object Name
Get-ChildItem -LiteralPath $AdmixBin -Filter '*.dll' | Select-Object Name
```

Use **`$Repo\bin`**, not another port's `build\bin\separate` folder. Each program
has its own `.exe`; there is no combined dispatcher. Build metadata covers the
selected targets, so inspect `executables` if you previously built only a subset.
The metadata's `parity_validated` flag is not a substitute for recorded Linux
comparisons; a successful compilation alone does not certify numerical parity.

For a portable local copy, copy the complete contents of `bin` to a user-writable
folder, retaining the adjacent DLLs, `script` and `licenses` directories and
metadata. Keep `qpAdm.exe` and `qpfstats.exe` together. The native tools can then
run without MSYS2, but helper scripts still need their own interpreters. This is
manual deployment of a development build, not an MSI installer or a published
binary release.

Each tool reserves an 8 MiB main-thread stack, matching the tested Linux
reference's allowance. The compatibility-method review and its exclusions are
recorded in [WINDOWS_PORT_REVIEW.md](WINDOWS_PORT_REVIEW.md).

To rebuild, run the same command. Objects are reused only when the source,
shared headers, compiler and flags match. Linux/macOS objects are kept separate
from `src/.windows/`. Use the existing `src/Makefile` or `src/Makefile.mac` for
those platforms.

## 5. Run from PowerShell

Before changing PATH, use an explicit path:

```powershell
$AdmixBin = (Resolve-Path -LiteralPath (Join-Path $Repo 'bin')).Path
& (Join-Path $AdmixBin 'qpAdm.exe') -h
& (Join-Path $AdmixBin 'qpWave.exe') -h
```

PowerShell does not search the current directory for an executable automatically.
Use `./` or `.\` for a local executable, or the call operator `&` for a quoted
path/variable. For example, `$Exe = Join-Path $AdmixBin 'qpAdm.exe'` followed by
`& $Exe -p 'qpAdm.par'` invokes the actual binary.

Use each program's upstream help and parameter documentation. Some older tools
have different options and do not implement `-h`. Version codes retain their
upstream number and add `.w` on Windows; this baseline's `qpAdm` is `2206.w`.
There is no extra banner or automatic log file.

Compressed genotype inputs ending in `.gz` are supported through native
[zlib](https://zlib.net/manual.html) decompression. No Unix `gunzip` installation
is needed. The build includes the native zlib DLL (`libz-1.dll` in the tested
toolchain) and its license with the other runtime
files. Text EIGENSTRAT, packed, transposed packed and ANCESTRYMAP gzip inputs
have been compared against Linux. Concatenated gzip members are supported;
damaged or truncated streams are rejected before analysis.

The upstream `unzip cmd: gunzip -c ...` terminal line is retained for output
compatibility; Windows performs that decompression internally. Generated paths
use native backslashes. Temporary decompressed files are removed after a
successful read or detected decompression failure. Owned-file cleanup also has
recorded fatal-reader checks; forced process termination or power loss cannot
guarantee cleanup. Open edge cases in individual tools' audits remain separate.
For large inputs, ensure the temporary directory has space for the uncompressed
file. To create and select a directory for this PowerShell session:

```powershell
$TempDir = Join-Path $env:LOCALAPPDATA 'AdmixTools\temp'
New-Item -ItemType Directory -Path $TempDir -Force -ErrorAction Stop | Out-Null
$env:STMP = $TempDir
```

You can choose a folder on another existing drive if it has more free space.
`STMP` is an environment variable inherited by the native processes, not a
dataset prefix. Closing this terminal discards this session-only setting.

For an analysis, put your data and parameter files in an analysis directory:

```powershell
$AnalysisDir = 'C:\genomics\analysis'  # Change to your existing analysis folder.
Set-Location -LiteralPath $AnalysisDir
& (Join-Path $AdmixBin 'qpAdm.exe') -p .\par.qpAdm
$LASTEXITCODE
```

The source download does not include your genotype dataset. For an EIGENSTRAT
prefix `D:\genomics\cohort`, expect **three files**: `cohort.geno`, `cohort.snp`
and `cohort.ind`. The prefix has no extension. Ensure Windows Explorer is showing
file extensions so `qpAdm.par` is not accidentally saved as `qpAdm.par.txt`.
Population names must match the dataset exactly, including punctuation/case.

A minimal parameter file has the usual upstream keys:

```text
genotypename: cohort.geno
snpname: cohort.snp
indivname: cohort.ind
popleft: left.txt
popright: right.txt
seed: 77
```

`left.txt` and `right.txt` contain population names, one per line; those names
must match the `.ind` file. Follow `README.qpWave` and upstream qpAdm guidance
when constructing a scientifically meaningful model.

Relative paths in parameter files are resolved from the **current working
directory**, not automatically from the parameter file's directory. Keeping
parameter and data names relative also makes workflows easier to use on Linux.
Use the call operator `&` when invoking an executable whose path is quoted.

For Windows string parameters containing spaces, quote the value:

```text
genotypename: "C:/genomics/my data/cohort.geno"
```

Quoted string parameters are a Windows compatibility extension; upstream's
unquoted parser reads the first whitespace-separated token. Forward slashes
work in native Windows paths. Recorded Windows checks cover Unicode/quoted and
long temporary paths; they do not certify every reader, UNC share or machine
policy. The manifest opts into long paths, but
[Windows policy also applies](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation).
This build does not change your registry or system code page.
`allsnps: YES` precomputation locates `qpfstats.exe` beside
the parent program; keep the suite together when copying it.

For a parameter file shared directly with pristine Linux, prefer short relative
filenames without spaces or Windows-only quoting, and stage the same inputs on
each platform. A Windows drive path is not automatically translated into a WSL
or Linux path.

Generated temporary paths use native Windows backslashes, for example
`tmp: C:\Users\USERNAME\AppData\Local\Temp\fsx.12345`, including when a temporary
directory override was supplied with forward slashes.

Ordinary text log redirection:

```powershell
& (Join-Path $AdmixBin 'qpAdm.exe') -p .\par.qpAdm > .\qpAdm.log 2> .\qpAdm.err
$LASTEXITCODE
```

PowerShell versions can re-encode redirected native text. For byte-preserving
logs in Windows PowerShell 5.1, use command-shell redirection:

```powershell
cmd.exe /d /c 'qpAdm -p par.qpAdm > qpAdm.log 2> qpAdm.err'
$LASTEXITCODE
```

The last example assumes `qpAdm` is on PATH as described in section 6. It saves
stdout and stderr separately without PowerShell's text-file re-encoding.
Windows PowerShell 5.1 typically writes redirected/Tee text logs as UTF-16;
PowerShell versions have different encoding behavior, and PowerShell 7.4+ has
specific native byte-preserving redirection rules. See Microsoft's
[redirection documentation](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_redirection).
Do not assume a text pipeline preserves native bytes in every version.

Program-generated genotype files are written directly in binary mode. Do not
pipe binary output through PowerShell text commands such as `Out-File`.

### Write parameters as UTF-8

For parameters/population lists, use UTF-8 without a BOM so the same files can
also be used with pristine Linux. Windows accepts an initial UTF-8 BOM, but that
is a Windows extension. Avoid PowerShell 5.1's default `Out-File` for these inputs:
it writes UTF-16. VS Code's **Save with Encoding → UTF-8** is one option; the
complete example below uses the .NET API explicitly. Do not assume `-Encoding
utf8` means the same BOM behavior in Windows PowerShell 5.1 and PowerShell 7.

For non-ASCII terminal text in a normal PowerShell console, you can set:

```powershell
$Utf8Console = New-Object System.Text.UTF8Encoding $false
[Console]::OutputEncoding = $Utf8Console
$OutputEncoding = $Utf8Console
```

This changes the current console/pipeline encoding, not the encoding of existing
files or the machine locale. Native output still goes to stdout/stderr without
an automatic application log.

### Complete qpAdm job example

Edit **the binary folder, dataset prefix and population names** first. The names
below are placeholders, not a recommended scientific model. LEFT starts with
the target, followed by sources; RIGHT contains the reference populations.
The model and switches must be chosen for your analysis. `allsnps: YES` and
`inbreed: NO` are explicit example choices, not changed program defaults.

This block works before PATH configuration. It checks inputs, creates a fresh
job directory, writes UTF-8 inputs, runs from the directory containing the
relative population filenames, displays/saves text output, measures elapsed
time and checks the native exit code. It does not overwrite an existing job.

```powershell
# Native Windows PowerShell 5.1 / PowerShell 7
$AdmixBin = Join-Path $env:USERPROFILE 'source\AdmixTools_Win\bin'
$DataPrefix = 'D:\genomics\data\cohort'  # No .geno/.snp/.ind extension here.
$JobRoot = Join-Path $env:USERPROFILE 'AdmixToolsJobs'
$JobName = 'qpAdm_demo'

$AdmixBin = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($AdmixBin)
$DataPrefix = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($DataPrefix)
$JobRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($JobRoot)
$Exe = Join-Path $AdmixBin 'qpAdm.exe'
$JobDir = Join-Path $JobRoot (('{0}_{1}' -f (Get-Date -Format 'yyyyMMdd_HHmmss_fff'), $JobName))

foreach ($InputFile in @(
    $Exe
    (Join-Path $AdmixBin 'qpfstats.exe')
    "${DataPrefix}.geno"
    "${DataPrefix}.snp"
    "${DataPrefix}.ind"
)) {
    if (-not (Test-Path -LiteralPath $InputFile -PathType Leaf)) {
        throw "File not found: $InputFile"
    }
}

New-Item -ItemType Directory -Path $JobRoot -Force -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $JobDir -ErrorAction Stop | Out-Null
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllLines((Join-Path $JobDir 'LEFT.pops'), @(
    'Target'
    'Source1'
    'Source2'
), $Utf8NoBom)
[System.IO.File]::WriteAllLines((Join-Path $JobDir 'RIGHT.pops'), @(
    'Outgroup'
    'Right1'
    'Right2'
    'Right3'
), $Utf8NoBom)
[System.IO.File]::WriteAllLines((Join-Path $JobDir 'qpAdm.par'), @(
    ('genotypename: "{0}.geno"' -f $DataPrefix)
    ('snpname: "{0}.snp"' -f $DataPrefix)
    ('indivname: "{0}.ind"' -f $DataPrefix)
    'popleft: LEFT.pops'
    'popright: RIGHT.pops'
    'seed: 77'
    'details: YES'
    'allsnps: YES'
    'inbreed: NO'
), $Utf8NoBom)

Push-Location -LiteralPath $JobDir -ErrorAction Stop
try {
    Write-Host "Job folder: $JobDir"
    $Timer = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        & $Exe -p 'qpAdm.par' 2>&1 | Tee-Object -FilePath 'result.txt'
        $RunExitCode = $LASTEXITCODE
    }
    finally {
        $Timer.Stop()
        Write-Host "Elapsed: $($Timer.Elapsed)"
    }
    if ($RunExitCode -ne 0) {
        throw "qpAdm exited with code $RunExitCode. Read $JobDir\result.txt"
    }
}
finally {
    Pop-Location
}
```

The `.par`/population files use UTF-8 without a BOM; adapt the Windows paths and
quoting before reusing parameters on pristine Linux. `result.txt` is a PowerShell
text log and can use a different encoding. `$LASTEXITCODE` must be captured immediately
after the native run/pipeline; another native command can replace it. Inherited
Linux errors or invalid models are not fixed by this tutorial. Error text can
appear as a PowerShell `NativeCommandError`; inspect the tool's diagnostic and
exit code, not only the console color. For separate raw streams, use the
command-shell redirection shown above.

## 6. Add the suite to your user PATH

From the repository root, these commands update your user PATH, retaining other
entries, and make it available in the current PowerShell session:

```powershell
$AdmixBin = (Resolve-Path -LiteralPath (Join-Path $Repo 'bin')).Path
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$BackupDir = Join-Path $env:LOCALAPPDATA 'AdmixTools\path-backups'
New-Item -ItemType Directory -Path $BackupDir -Force -ErrorAction Stop | Out-Null
$PathBackup = Join-Path $BackupDir (('user-path-{0}.txt' -f (Get-Date -Format 'yyyyMMdd_HHmmss_fff')))
[System.IO.File]::WriteAllText($PathBackup, [string]$userPath, (New-Object System.Text.UTF8Encoding $false))
$otherEntries = @($userPath -split ';' | Where-Object {
    $_ -and $_.Trim().TrimEnd('\') -ine $AdmixBin.TrimEnd('\')
})
[Environment]::SetEnvironmentVariable('Path', ((@($AdmixBin) + $otherEntries) -join ';'), 'User')
$env:Path = "$AdmixBin;$env:Path"
Write-Host "Previous user PATH saved to: $PathBackup"
Get-Command qpAdm -All
qpAdm -h
```

Add the **`bin` directory**, not an individual `.exe`, the repository root or
MSYS2's directory. This changes the user PATH only and does not require an
Administrator terminal. Running this again replaces the matching user entry
rather than accumulating case/trailing-backslash duplicates. The temporary
`$env:Path` assignment above is what makes it work in the already open terminal.

New terminals inherit the saved user PATH. `Get-Command qpAdm -All` reveals
competing installations. Check that it resolves to this checkout; an older
system-wide installation can take precedence. An explicit executable path
always selects the intended build. If you later move the checkout, update PATH
to the new `bin` location.

If a terminal is launched by an already running VS Code or another terminal
application, restart that parent application if it still inherits the old PATH.
An older System PATH entry can also take precedence over a User PATH entry;
inspect `Get-Command qpAdm -All` and use the explicit executable path until the
conflict is resolved.

If you prefer the Windows interface, search Start for **Edit environment variables
for your account**, edit the user's **Path**, add a new entry containing the full
`bin` path, save, and reopen your terminal. Do not replace the entire PATH with
just the AdmixTools folder.

## 7. Verify the build

### Check that the expected binary launches

```powershell
$AdmixBin = (Resolve-Path -LiteralPath (Join-Path $Repo 'bin')).Path
& (Join-Path $AdmixBin 'qpAdm.exe') -h
$LASTEXITCODE
```

A successful help invocation confirms the executable can load its basic runtime
dependencies. It does not verify the scientific calculations or all helper tools.
Use a complete build; metadata from a selected-target build is not evidence that
all 37 binaries were rebuilt.

### Run the self-contained synthetic cases

The self-contained integration suite creates synthetic data and records raw
streams and generated files:

```powershell
Set-Location -LiteralPath $Repo
$CheckId = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$WindowsCheck = Join-Path $Repo "validation-results\windows-$CheckId"
python tests/windows/parity.py --bin bin --output $WindowsCheck
$LASTEXITCODE
```

A fixture runner completing is not sufficient on its own: inspect its manifest
for missing executables, timeouts and unsuccessful runs. The suite has an
intentional `transpose-invalid` failure case (exit 64). Its comparison step checks
the expected statuses, output streams, generated files and binary round trips.
This does not download or modify your analysis dataset.

A run on Windows alone is a functional check, not proof of Linux parity. Follow
[tests/windows/README.md](tests/windows/README.md) to build the pinned pristine
Linux reference and compare:

```powershell
$LinuxCheck = 'C:\path\to\the\retained\pristine-linux-results'  # Replace this.
python tests/windows/parity.py --compare $LinuxCheck $WindowsCheck
$LASTEXITCODE
```

The Linux results must come from the same fixture runner, upstream commit and
controlled seed/thread settings. They are not any arbitrary qpAdm log. Read the
generated `comparison.json` and `comparison.diff`; do not hide scientific
differences with a tolerance or substitute a repaired Linux build for pristine
upstream. WSL is optional for ordinary installation/running and only needed if
you choose it to produce the Linux reference locally.

For the current port-only scope, the reference builder and further cases are in
`tests/windows/port_only_scope.py`. Its `--build-linux` option belongs in WSL and
requires Linux compiler/library dependencies described by the validation docs.
Its comparison command retains differences for review and does not itself turn
every mismatch into a nonzero process exit. Older corrective-audit `--verify`
runners can require archived, beyond-scope fixes; they are not the current
compatibility contract. See the
[scope restoration report](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md).

Scientific results and generated files are compared exactly, without numerical
tolerances. The allowed platform metadata exceptions and tested tool list are
recorded in [WINDOWS_PORT_STATUS.md](WINDOWS_PORT_STATUS.md). Use a new output
directory for each run. Wider datasets, platforms and dependency combinations
are release work, not implied by the initial passing cases.

## 8. Troubleshooting

- **`python`/`git` is not recognized or opens an unexpected application:** reopen
  PowerShell after installation, use `Get-Command python, git -All`, and correct
  PATH/App execution aliases. The private argp environment does not replace the
  normal `python` command used by the build entry point.
- **`pacman` is not recognized:** you are probably in PowerShell. Run package
  installation/update commands in **MSYS2 UCRT64**, then return to PowerShell.
- **The script cannot run / execution policy error:** use the section 3/4
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...` invocation after
  reviewing the local script. Do not change the permanent machine execution
  policy as a prerequisite. Organization policy can still apply.
- **GCC not found:** check `C:\msys64\ucrt64\bin\gcc.exe` and the
  `-Msys2Root` argument. Install the UCRT64 GCC package in the MSYS2 terminal.
- **Missing GSL/OpenBLAS headers or libraries:** install both matching UCRT64
  packages. Do not mix toolchains or copy arbitrary DLLs from another port.
- **Missing zlib header/library or its DLL:** install the UCRT64 zlib package
  listed above and rebuild. Keep the copied DLL beside the executables.
- **GNU argp missing:** run `prepare-windows.ps1` before the full build.
- **`windres`/`ar`/`objdump` missing:** install UCRT64 binutils and use the same
  `-Msys2Root` value for preparation and compilation.
- **pip/download/TLS errors during preparation:** verify normal internet access,
  proxy/certificate settings and the complete error log. Preparation downloads
  pinned Python build dependencies and an argp Git checkout. Do not disable TLS
  checks or silently change the pinned revision to get past the error.
- **A missing-DLL message when starting a program:** rebuild and keep the copied
  DLLs beside the `.exe` files. Adding just the source directory to PATH is not
  sufficient.
- **Linker cannot replace an executable:** close that program and wait for any
  running validation job to finish before rebuilding.
- **A file cannot be opened:** check the current directory, parameter spelling,
  quoted paths with spaces, and actual data filenames. The example data are not
  bundled with the source; see upstream's `README` for its download link.
- **`LEFT.pops` / `RIGHT.pops` cannot be opened although `-p` names an absolute
  file:** change into the job directory before running. Relative values inside
  the parameter file resolve against the working directory. Check for hidden
  `.txt` extensions and UTF-16 encoding too.
- **`qpfstats failure` in an all-SNP run:** check that the sibling `qpfstats.exe`
  and DLLs exist, the data/population paths are valid, and the temporary directory
  exists and is writable. Use an upstream-supported helper-log parameter where
  available and consult that tool's audit for known error-path limitations.
- **A path containing spaces or `#` is cut off:** quote the entire string value
  in the parameter file. Quoting only the executable invocation does not quote
  filenames written inside `.par` files.
- **Garbled text, suspicious parameter names or empty input:** save parameters
  and lists as UTF-8 without BOM. The console setting does not convert a file
  previously written as UTF-16. Prefer the .NET write example above.
- **The run appears idle:** large genotype reads, qpfstats precomputation and
  upstream rejection sampling can take time without progress updates. Inspect
  Task Manager, the active output and disk space. This port does not add an
  automatic sampling cap or progress banner; an inherited Linux problem is
  documented separately from a Windows porting regression.
- **Different results:** record both upstream commits, seeds, compiler/library
  versions, flags, inputs and thread settings. Use the comparison runner and
  inspect its diff before changing any computation or tolerance.
- **Graph rendering or interpreter helper fails:** install the requested
  external tool separately. Native `qpreroot` rendering and the Python
  conversion/extraction/merge/hash workflow are tested as described below.
  Other shell/Perl/R helper workflows still need validation.

### Optional graph rendering

`qpreroot -d graph.dot` can generate the DOT source and a PDF using native
Graphviz and Ghostscript. These optional programs are separate installations;
they are not copied into AdmixTools' `bin/`. For the tested MSYS2 UCRT64 setup,
install from the **UCRT64 terminal**:

```bash
pacman -S --needed mingw-w64-ucrt-x86_64-graphviz
```

The [UCRT64 Graphviz package](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-graphviz)
pulls native Ghostscript and its runtime dependencies. In the
PowerShell session used for rendering, add their directory to the process PATH:

```powershell
$env:PATH = "$(Join-Path $Msys2Root 'ucrt64\bin');$env:PATH"
& (Join-Path $AdmixBin 'qpreroot.exe') -g .\graph -d .\graph.dot
```

Adjust the MSYS2 directory if necessary. Separate Windows installations also
work when `dot.exe` and `gswin64c.exe` (or `gs.exe`) are on PATH. The port invokes
these executables directly, without a Unix shell or `ps2pdf` batch script. Like
upstream `ps2pdf` with one input, the PDF is written in the working directory
using the input basename. The intermediate `.ps` file is removed. The original
graph and DOT bytes match Linux in the fixture; PDF bytes/layout can differ with
renderer versions, timestamps and fonts. Upstream does not propagate rendering
failure as an analysis exit failure, so check stderr and the PDF's existence.

### Python conversion and extraction helpers

Invoke installed scripts explicitly with Python, for example:

```powershell
python .\bin\script\convertf.py -i 'C:\data\cohort' -o 'C:\results\cohort' -f transpose_packed
python .\bin\script\extract_individuals.py -i 'C:\results\cohort' -o 'C:\results\subset' Sample1 Sample2
python .\bin\script\hash_checks.py 'C:\results\subset.geno'
```

Use these script locations so they find this build's sibling executables.
The tested workflow converts, extracts, merges and checks hashes, with 12 output
files matching Linux byte-for-byte. Quoted Windows parameter paths and LF data
files are retained. If Windows denies SNP symlink creation specifically because
the required privilege is absent, extraction copies the same SNP bytes instead.
Other filesystem errors are still reported. Perl/R helpers and additional
external-tool workflows remain separate work; copying them does not establish
that every script is Windows-compatible.

### qp4diff

Run the native executable from PowerShell and redirect its results from stdout:

```powershell
& .\bin\qp4diff.exe -p '.\parameters with spaces' > .\qp4diff.log 2> .\qp4diff.err
$LASTEXITCODE
```

The parameter file needs `genotypename`, `snpname`, `indivname` and
`popfilename`, or `instem` in place of the three data paths. Each population-list
row has eight names: `A B C D : E F G H`. Colons are optional. The statistic is
`firstf4mult * f4(A,B;C,D) - f4(E,F;G,H)`, with its joint block-jackknife error.
`firstf4mult` defaults to 1. `blgsize` is in **Morgans**, with default 0.05.
Default `overlap: YES` uses sites valid for both quartets. `allsnps: YES`
selects separate site sets; `allsnps: NO` selects shared sites and overrides
`overlap`. This tool defaults to `fancyf4: NO`.

The pinned upstream has quirks preserved by this compatibility port:
`output:`/`outputname:` truncate a named file but leave results on stdout;
use shell redirection. `-v` prints the version and continues if `-p` is also
given, despite its inherited help text. `seed`, `chrom`, `xdata`, `noxdata`,
`inbreed`, `jackweight` and `blockname` are not parsed controls here.
`popsizelimit` uses an analysis index built before limiting and is unreliable.
Long population-list rows can corrupt memory on both Linux and Windows.
These are deferred upstream findings, not new Windows behavior. The
[T07 audit](tests/windows/audits/T07_qp4diff.md) records exact tested modes,
comparisons, remaining coverage and the isolated validated executable location.

### qpGraph

Run the native executable directly and redirect its scientific output:

```powershell
& .\bin\qpGraph.exe -p '.\graph parameters' > .\qpGraph.log 2> .\qpGraph.err
$LASTEXITCODE
```

Use `graphname:` for the graph and `fstatsname:` for an existing qpfstats file.
With no `fstatsname`, qpGraph runs its sibling `qpfstats.exe` using the genotype,
SNP and individual paths in the parameter file; keep both executables and their
DLLs together. Graph populations and the fstats base population must agree.
Use the same explicit seed, inputs, parameters and dependency/thread settings
when comparing with Linux. Windows accepts quoted parameter paths with spaces
and either slash direction; generated Windows temporary paths use backslashes.

`graphoutname`, `graphdotname`, `dumpname`, `admixout`, `f3log` and `outliername`
select their upstream output files. qpGraph writes DOT source; optional rendering
is a separate qpreroot workflow. `output:` truncates its file without placing
the terminal results there; use PowerShell redirection. Inherited CLI quirks
remain: `-h` is advertised but rejected, and `-v` continues when `-p` is supplied.
Parameter-file values override corresponding command-line values.

The [T08 audit](tests/windows/audits/T08_qpGraph.md) records successful finite
fits matching pristine Linux, the isolated validated binary, and the remaining
limits. Half-score currently fails in the pinned upstream and is not validated
for scientific use. Damaged gzip and failed-child/missing-output paths retain
open Windows compatibility differences. These findings do not change upstream
calculation defaults, input acceptance or exit behavior to repair Linux bugs.

## 9. Updates and removal

### Update an installed source checkout

Keep your analysis data outside the source tree. Inspect the checkout first:

```powershell
Set-Location -LiteralPath $Repo
git status --short
git branch --show-current
```

If you are on `main`, have no local changes to preserve, and intend to
update from that published branch, use:

```powershell
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed.' }
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw 'Update did not fast-forward; preserve and review local work.' }
```

Do not use a hard reset or `git clean` as an update step. If you are on a topic
branch or have local commits/edits, preserve and review that work separately.
Updating source does **not** automatically replace the executables. Stop running
analyses, repeat preparation when needed, rebuild with section 4, then rerun
verification and inspect the new build metadata. Existing job folders are not
rebuilt or modified by a source update.

For dependency updates, use the full MSYS2 update in section 1. A new dependency
combination needs its own validation; packages are rolling releases and are not
all pinned by this repository. For a fully fresh generated build, close running
jobs and rename **only `src\.windows`** to a backup name in File Explorer, then
repeat sections 3 and 4. That directory contains generated objects, argp and its
private Python environment; keep your source and dataset files. Preserve old
build metadata if you need to reproduce an earlier analysis.

Upstream synchronization is a separate maintainer task: preserve local work,
fetch `upstream`, merge the selected tracking revision into `main`,
resolve compatibility changes, update `UPSTREAM_BASELINE` and rerun pristine
Linux comparisons. Keep `master` as the upstream tracking line. Its historical
illegal Windows filenames require special handling; a separate reference tree
on the Linux/WSL filesystem is convenient. Do not switch an ordinary Windows
checkout to upstream `master` as part of a routine install.

### Move or remove this manual installation

There is currently no installer or uninstall entry. To remove your PATH entry:

```powershell
$AdmixBin = Join-Path $env:USERPROFILE 'source\AdmixTools_Win\bin'  # Use the OLD installed path.
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$remaining = @($userPath -split ';' | Where-Object {
    $_ -and $_.Trim().TrimEnd('\') -ine $AdmixBin.TrimEnd('\')
})
[Environment]::SetEnvironmentVariable('Path', ($remaining -join ';'), 'User')
$env:Path = (($env:Path -split ';' | Where-Object {
    $_ -and $_.Trim().TrimEnd('\') -ine $AdmixBin.TrimEnd('\')
}) -join ';')
```

Reopen other terminals afterwards and inspect `Get-Command qpAdm -All`. For a
move, remove the old entry, copy the complete suite to its new folder, and add
that new `bin`/runtime folder using section 6. A user PATH backup was saved under
`%LOCALAPPDATA%\AdmixTools\path-backups` when using the scripted setup above;
review it before using it to restore an entire old PATH, since later unrelated
PATH changes could otherwise be lost.

Close programs using this build before removing its generated files or checkout
through File Explorer. Keep analysis data, parameters, logs and any build
metadata/backups you still need. Do not uninstall a shared MSYS2/Python/Git
installation just to remove AdmixTools; other software can depend on it.
The MSI milestone will add a chosen installation location, build/dependency
provisioning, PATH integration, upgrades, repair and uninstall after the numerical
compatibility baseline is ready.

## What was checked for this guide

The commands were reviewed against `prepare-windows.ps1`, `build-windows.ps1`
and `src/build_windows.py`. PowerShell examples were syntax-checked with Windows
PowerShell 5.1, and the complete job example was exercised using synthetic
fixture data and this checkout's existing native binaries. No fresh MSYS2 or
Windows installation was performed for this documentation change, and no
machine/user PATH or execution-policy setting was changed while validating it.
Dependency installation follows the official pages linked above; the historical
compiler/library and Linux comparison evidence remains in the audit reports.

## Windows filename mapping and recovery history

The original clone used non-cone sparse checkout to exclude 11 colon-containing
paths. The following replacements are byte-for-byte copies, kept in the same
upstream directories. Historical filenames inside reference logs are preserved.

| Original path | Windows-compatible copy |
| --- | --- |
| `examples.qpGraph/gr1x:log:nullout` | `examples.qpGraph/gr1x_log_nullout` |
| `examples.qpGraph/par:sim1:gr1triv` | `examples.qpGraph/par_sim1_gr1triv` |
| `examples.qpGraph/par:sim1:gr1x` | `examples.qpGraph/par_sim1_gr1x` |
| `examples.qpGraph/par:sim1:gr1x:2` | `examples.qpGraph/par_sim1_gr1x_2` |
| `examples.qpGraph/par:sim1:gr1x:nullout` | `examples.qpGraph/par_sim1_gr1x_nullout` |
| `examples/gr1triv:log` | `examples/gr1triv_log` |
| `examples/gr1x:2:log` | `examples/gr1x_2_log` |
| `examples/gr1x:log` | `examples/gr1x_log` |
| `examples/xx:qp4diff` | `examples/xx_qp4diff` |
| `examples/xx:qp4diffa` | `examples/xx_qp4diffa` |
| `examples/xx:qpff3` | `examples/xx_qpff3` |

Four files are qpGraph parameters and seven are reference logs. The existing
`runit`, `runqpgf`, and `runqpgf2` scripts use the underscore names, including
Windows-compatible generated graph/log names. They remain shell/Perl scripts.

The replacements and removal of the original colon paths are committed in
`9bfd9ee` on the published port branch, so fresh Windows checkouts can use the
ordinary layout. This clone's local
`.git/info/sparse-checkout` exclusions remain useful when switching to the
upstream tracking branch, which retains the original names.

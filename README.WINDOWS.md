# ADMIXTOOLS on Windows

This is a native 64-bit Windows compatibility port of
[DReichLab/AdmixTools](https://github.com/DReichLab/AdmixTools), keeping the
upstream source layout, separate program names and numerical algorithms.
The first goal is matching Linux results and terminal output. Optimizations and
a standard MSI installer are later milestones.

**Development status:** 37 executables build; 35 integration cases across 26
tools have been compared with a pinned Linux reference. Full-suite parity has
not yet been established. See [WINDOWS_PORT_STATUS.md](WINDOWS_PORT_STATUS.md)
for exact coverage and remaining work. Development is published on the
[`windows-port` branch](https://github.com/nomanfinally/AdmixTools_Win/tree/windows-port).
The per-tool hard compatibility audit is underway. The
[T01 qpAdm report](tests/windows/audits/T01_qpAdm.md) records its mode checks,
Windows fixes, upstream bug fixes and remaining limits. This is a development
source publication, with no release or MSI installer yet.

The [T02 qpfstats report](tests/windows/audits/T02_qpfstats.md) and its
[corrections](tests/windows/audits/T02_qpfstats.corrections.md) record direct
modes, formats and helper/consumer checks. T02 has **passed with limitations**:
population limits and seeds now affect the selected analysis, qpfit reaches its
existing fitting code, and shared helper files are cleaned up. These explicit
upstream bug corrections intentionally change broken behavior; comparisons use
both a pristine reference and a separately corrected Linux build.

For the sequential per-tool/module bug and compatibility review, see
[COMPATIBILITY_AUDIT.md](COMPATIBILITY_AUDIT.md). Existing fixture coverage does
not count as a completed hard audit.

The [T05 qp3Pop corrections](tests/windows/audits/T05_qp3Pop.corrections.md)
close all 14 recorded finding groups in their tested scopes. T05 has passed
with limitations: 167 Windows/Linux/sanitizer cases pass, including independent
X and large-inbred-count oracles. All 37 supported binaries have been rebuilt;
the previous bin bytes are preserved under the recorded repair artifacts.
Seeded and mixed-X results intentionally differ from broken pristine behavior.

On X, declared F records are diploid; M/U retain the haploid convention, with
heterozygous calls excluded. Supply correct sex labels; inbreed does not infer
sex. A zero target-heterozygosity denominator is rejected. `outgroupmode: YES`
uses upstream's arbitrary `.001` denominator and still requires the applicable
inbreed/override setting for a target without heterozygotes. SNP details now
retain all triples in input order, using the existing fields without separator
headers; write failures are fatal. Ordinary results go to stdout. Inactive
`output:`/`outputname:`/`f3log:` and legacy controls reject explicitly. Use
PowerShell redirection as shown below and inspect stderr and `$LASTEXITCODE`.

The [T06 compatibility review](tests/windows/audits/T06_scope_restoration.md)
keeps inherited Linux behavior. Its upstream-bug repairs are deferred and were
removed from active source/binaries; the Windows-only CLI diagnostic fix remains.
Known inherited issues include ineffective population limits/seed settings,
X counting, malformed lists and undefined estimates. `output:`/`outputname:`
can truncate an existing file without writing results: omit them and redirect
stdout in PowerShell. These issues are recorded, not repaired at this stage.
Earlier tools' changes remain untouched; this is not full-suite pristine parity.

For qpF4ratio, each population row has eight names: four for the numerator f4,
then four for the denominator. `blgsize` is in **Morgans** (`0.05` = 5 cM),
despite the unit wording in the upstream README. `diffmode: YES` pairs the first
half of rows with the second half and computes **alpha A + alpha B - 1**.
Supply an even, nonzero number of rows; upstream silently ignores an unpaired
final row. Keep population-list lines short: the inherited fixed-buffer parser
has a recorded long-line defect. Preserve upstream `zzblock:` output in logs.

## 1. Prerequisites

Use 64-bit Windows 10 version 1903 or later, or Windows 11, PowerShell,
Git for Windows and Python 3.10 or later. The current audit ran on Windows 11
with Windows PowerShell 5.1; other Windows versions need their own validation.
The initial development build was tested with Python 3.13 and MSYS2 UCRT64 GCC
16.2.0. Check that the real Python interpreter is available:

```powershell
git --version
python --version
```

Install [MSYS2](https://www.msys2.org/) following its
[official installer instructions](https://www.msys2.org/docs/installer/).
The examples below assume `C:\msys64`; a custom location also works. Open the
**MSYS2 UCRT64** terminal and update it:

```bash
pacman -Syu
```

If the updater closes the terminal or asks you to restart it, reopen UCRT64 and
run that command again. Install the native compiler and scientific libraries:

```bash
pacman -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-gsl mingw-w64-ucrt-x86_64-openblas mingw-w64-ucrt-x86_64-zlib
```

Use the UCRT64 packages together. Do not substitute the MSYS `/usr/bin/gcc`
compiler or mix MINGW64/CLANG64 libraries with UCRT64. The build runs from
PowerShell; MSYS2 supplies the compiler and libraries. The resulting programs
run without an MSYS shell or WSL.

## 2. Obtain the source and choose a branch

For this existing workspace:

```powershell
Set-Location C:\work\AdmixTools_Win
git switch windows-port
```

Use `windows-port` for the maintained port and keep `master` as the upstream
tracking line. Create small topic branches from `windows-port` for later fixes.
The configured remotes are:

```text
origin    https://github.com/nomanfinally/AdmixTools_Win.git
upstream  https://github.com/DReichLab/AdmixTools.git
```

A fresh Windows checkout of the published port can use:

```powershell
git clone --branch windows-port https://github.com/nomanfinally/AdmixTools_Win.git
Set-Location AdmixTools_Win
```

The port branch contains the narrow filename renames needed for a Windows
checkout. The original upstream revision contains 11 names with colons, which
ordinary Windows checkouts cannot create. The mapping is listed below; the
upstream directory layout is retained. `master` remains the upstream tracking
line, so select `windows-port` explicitly when cloning or browsing this fork.

## 3. Prepare GNU argument parsing

From the repository root in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\prepare-windows.ps1 -Msys2Root C:\msys64
```

This creates a local Python environment under `src/.windows/`, installs pinned
Meson/Ninja build tools, fetches a pinned GNU argp source revision, builds it and
runs its included tests. This is needed by `transpose` and `merge_transpose` to
retain GNU command-line parsing and help. It does not change the system Python,
user PATH, or persistent PowerShell execution policy.

The preparation step needs internet access. Build dependencies and objects under
`src/.windows/` are generated and ignored by Git. See the pinned revision and
small diagnostic compatibility adjustment in `prepare-windows.ps1`.

## 4. Compile the suite

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-windows.ps1 -Msys2Root C:\msys64
```

For a different MSYS2 installation, pass its root directory, for example
`-Msys2Root C:\msys64`.
List the inventory without compiling:

```powershell
python src/build_windows.py --list
```

All 28 upstream default executables and 9 additional buildable targets are
installed in `bin/`. `qpfmvmix` is listed as blocked because its upstream source
is malformed. It is never silently replaced with a different implementation.

The build copies the required native DLLs into `bin/`. Keep these DLLs beside
the executables. It also copies upstream Perl/R/Python helpers into their usual
installed locations. Those scripts still need their respective interpreters;
they are not native executable conversions. `bin/windows-build.json` records
the baseline, compiler, flags, source hashes and runtime DLL hashes.

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
.\bin\qpAdm.exe -h
.\bin\qpWave.exe -h
```

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
successful read, decompression failure and the native Windows fatal-reader
cases exercised in T01/T02. Forced process termination is not covered. For large inputs, ensure the temporary
directory has space for the uncompressed file. To select an existing directory:

```powershell
$env:STMP = 'D:\AdmixToolsTemp'
```

For an analysis, put your data and parameter files in an analysis directory:

```powershell
Set-Location C:\genomics\analysis
& 'C:\work\AdmixTools_Win\bin\qpAdm.exe' -p .\par.qpAdm
$LASTEXITCODE
```

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

The [T04 corrections](tests/windows/audits/T04_qpDstat.corrections.md) repair all
23 recorded defects and an additional malformed numeric parameter defect.
Population limits now honor the seed; tree/Fourier memory errors and zero-statistic
SD output are corrected. Unsupported `output`/`outputname`, `colcalc`, `fullmode`,
`nostatslim`, `msjack` controls and `forceclade` fail explicitly. Use shell
redirection for output. Tree corrections requiring a single observed allele and
degenerate Fourier inputs are rejected; no replacement estimator is introduced.

CRLF macro substitution now works on Windows and Linux. Use UTF-8 parameter files;
LF and CRLF are tested. Forward-slash Windows input paths remain accepted.
The independent module/header audits remain incomplete, so T04 still has no
unqualified pass. The tested repair executables are isolated under
`validation-results/hard-check/T04/repairs/verified-builds/snapshot/bin`; the
previous installed `bin/` was preserved. Rebuild from the repaired source before
using the corrections through your normal PATH.

For Windows string parameters containing spaces, quote the value:

```text
genotypename: "C:/genomics/my data/cohort.geno"
```

Quoted string parameters are a Windows compatibility extension; upstream's
unquoted parser reads the first whitespace-separated token. Forward slashes
work in native Windows paths. T01 exercises Unicode genotype/parameter filenames,
a Unicode executable/helper directory, spaces, `&` and quoted `#` paths.
Every executable embeds a UTF-8 process manifest; save text inputs as UTF-8
(preferably without a BOM for compatibility with all upstream readers).
If an older PowerShell console displays Unicode names incorrectly, select UTF-8
for that console before invoking the tools:

```powershell
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
```

Windows qpAdm and qpfstats parameter files also accept an initial UTF-8 BOM; UTF-16/NUL
parameter files are rejected with an instruction to save as UTF-8.
Long-path cases pass on the audited machine with Windows long paths enabled.
The manifest opts in but does not change that machine policy; network/UNC paths
and every reader/tool are not certified by these tests.
`allsnps: YES` precomputation locates `qpfstats.exe` beside
the parent program; keep the suite together when copying it.

Generated temporary paths use native Windows backslashes, for example
`tmp: C:\Users\USERNAME\AppData\Local\Temp\fsx.12345`, including when a temporary
directory override was supplied with forward slashes.

Ordinary text log redirection:

```powershell
qpAdm -p .\par.qpAdm > .\qpAdm.log 2> .\qpAdm.err
$LASTEXITCODE
```

PowerShell versions can re-encode redirected native text. For byte-preserving
logs in Windows PowerShell 5.1, use command-shell redirection:

```powershell
cmd.exe /d /c 'qpAdm -p par.qpAdm > qpAdm.log 2> qpAdm.err'
```

Program-generated genotype files are written directly in binary mode. Do not
pipe binary output through PowerShell text commands such as `Out-File`.

For qpAdm helper diagnostics, set `fstatslog:` to a file and optionally
`keeptmp: YES`. The latter retains the temporary fstats, parameter, population,
filtered-parameter and default log files. Without it, owned files are removed
on normal completion and detected fatal input/helper errors. Forced termination
or power loss cannot be covered by ordinary process cleanup.

The T01 repairs intentionally correct broken upstream cases: single-source
coefficients, high-resolution/diagonal-only output, compressed PED/BED dispatch,
and invalid input/output handling. Read the report before comparing such cases
with an unpatched Linux binary. Ordinary supported fits retain upstream's
calculations and printed precision; optimization work remains deferred.

The [T01 follow-up corrections](tests/windows/audits/T01_qpAdm.corrections.md)
make `qpAdm -v` print the version and exit. `-V` enables verbose mode and `-d`
enables details. The inactive `output:`, `outputname:` and `maxrank:` parameters
now fail with guidance; save results through stdout redirection or `Tee-Object`.
For `newmode: YES` with `positive_coeffs: YES`, `maxreject:` limits consecutive
rejected proposals per sample (default 1,000,000; must be positive). Reaching it
fails the run explicitly without a partial Bayesian estimate. Always check
`$LASTEXITCODE`; inspect the model before increasing this limit. Accepted samples
retain the original calculations and RNG sequence.

For standalone f-statistic precomputation, use the upstream executable directly:

```powershell
.\bin\qpfstats.exe -p .\par.qpfstats > .\qpfstats.log 2> .\qpfstats.err
$LASTEXITCODE
```

Set `poplistname:` to a file with one population per line (at least two); the
first population is the basis. Set `fstatsoutname:` for the generated statistics,
and specify `allsnps:`, `inbreed:` and `scale:` explicitly as recommended in
`README.qpfstats`. `output:` is unsupported; use `fstatsoutname:` for the
statistics and PowerShell redirection for terminal text. `popsizelimit:` now
limits actual analysis individuals; `seed:` controls its selection. Seed 0 uses
the default sequence (equivalent to 1); a parameter-file seed overrides `-s`.
Individual IDs must be unique and `blgsize:` must be finite and positive.
Version remains `1101.w`. See the [T02 corrections](tests/windows/audits/T02_qpfstats.corrections.md)
for the known inactive keys and switches now rejected explicitly, intentional
differences from pristine upstream, and remaining validation limits.

qpWave's [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md) pass
with the documented limits. `popsizelimit:` now limits the actual individuals
analyzed; `seed:` controls selection using the existing RNG. Zero retains the
default sequence, equivalent to 1. This repairs broken upstream limited runs;
it does not make direct and all-SNP estimators interchangeable.

Use finite positive `blgsize:`, unique individual IDs and complete fstats files
from qpfstats. Malformed block labels, dimensions and cached statistics now fail
explicitly. qpWave rejects inactive `output:`, `outputname:`, `oldallsnpsmode:`,
`numboot:` and `details:` fields. Keep qpAdm/qpfit-only controls out of a qpWave
parameter file. Send results to a log using PowerShell redirection:

```powershell
.\bin\qpWave.exe -p .\par.qpWave > .\qpWave.log 2> .\qpWave.err
$LASTEXITCODE
```

`qpWave -v` now prints only its version and exits. Windows version remains
`2201.w`; numerical defaults and ordinary valid result formatting are retained.

## 6. Add the suite to your user PATH

From the repository root, these commands update your user PATH, retaining other
entries, and make it available in the current PowerShell session:

```powershell
$admixBin = (Resolve-Path .\bin).Path
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$otherEntries = @($userPath -split ';' | Where-Object { $_ -and $_ -ne $admixBin })
[Environment]::SetEnvironmentVariable('Path', (@($admixBin) + $otherEntries -join ';'), 'User')
$env:Path = "$admixBin;$env:Path"
Get-Command qpAdm -All
qpAdm -h
```

New terminals inherit the saved user PATH. `Get-Command qpAdm -All` reveals
competing installations. Check that it resolves to this checkout; an older
system-wide installation can take precedence. An explicit executable path
always selects the intended build. If you later move the checkout, update PATH
to the new `bin` location.

## 7. Verify the build

The self-contained integration suite creates synthetic data and records raw
streams and generated files:

```powershell
python tests/windows/parity.py --bin bin --output validation-results/windows
```

A run on Windows alone is a functional check, not proof of Linux parity. Follow
[tests/windows/README.md](tests/windows/README.md) to build the pinned pristine
Linux reference and compare:

```powershell
python tests/windows/parity.py --compare validation-results/linux validation-results/windows
```

Scientific results and generated files are compared exactly, without numerical
tolerances. The allowed platform metadata exceptions and tested tool list are
recorded in [WINDOWS_PORT_STATUS.md](WINDOWS_PORT_STATUS.md). Use a new output
directory for each run. Wider datasets, platforms and dependency combinations
are release work, not implied by the initial passing cases.

## 8. Troubleshooting

- **GCC not found:** check `C:\msys64\ucrt64\bin\gcc.exe` and the
  `-Msys2Root` argument. Install the UCRT64 GCC package in the MSYS2 terminal.
- **Missing GSL/OpenBLAS headers or libraries:** install both matching UCRT64
  packages. Do not mix toolchains or copy arbitrary DLLs from another port.
- **Missing zlib header/library or its DLL:** install the UCRT64 zlib package
  listed above and rebuild. Keep the copied DLL beside the executables.
- **GNU argp missing:** run `prepare-windows.ps1` before the full build.
- **A missing-DLL message when starting a program:** rebuild and keep the copied
  DLLs beside the `.exe` files. Adding just the source directory to PATH is not
  sufficient.
- **Linker cannot replace an executable:** close that program and wait for any
  running validation job to finish before rebuilding.
- **A file cannot be opened:** check the current directory, parameter spelling,
  quoted paths with spaces, and actual data filenames. The example data are not
  bundled with the source; see upstream's `README` for its download link.
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

That package pulls native Ghostscript and its runtime dependencies. In the
PowerShell session used for rendering, add their directory to the process PATH:

```powershell
$env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"
& 'C:\work\AdmixTools_Win\bin\qpreroot.exe' -g .\graph -d .\graph.dot
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

## 9. Updates and removal

Keep your analysis data outside the source tree. Before synchronizing upstream,
finish or preserve local changes, fetch `upstream`, and merge the upstream
tracking revision into `windows-port`. Resolve compatibility changes explicitly,
update `UPSTREAM_BASELINE`, rebuild, and rerun the Linux comparison. Keep
`master` available as the upstream tracking line. Upstream's historical illegal
filenames require special handling on Windows when switching to a pristine
upstream branch; a separate Linux/WSL reference checkout is convenient.

There is currently no installer or uninstall entry. To remove your PATH entry:

```powershell
$admixBin = 'C:\work\AdmixTools_Win\bin'
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$remaining = @($userPath -split ';' | Where-Object { $_ -and $_ -ne $admixBin })
[Environment]::SetEnvironmentVariable('Path', ($remaining -join ';'), 'User')
```

Close programs using this build before removing its generated files or checkout.
The MSI milestone will add a chosen installation location, build/dependency
provisioning, PATH integration, upgrades, repair and uninstall after the numerical
compatibility baseline is ready.

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

# Reproducing Linux/Windows comparisons

The current baseline is [port-only restoration](audits/PORT_ONLY_SCOPE_RESTORATION.md).
Use `parity.py`, `compatibility.py`, `script_helpers.py` and the new
`port_only_scope.py` for its recorded checks. For example:

```powershell
python tests/windows/port_only_scope.py --bin bin --output validation-results/port-only-new
python tests/windows/port_only_scope.py --compare validation-results/pristine-new validation-results/port-only-new
```

Run the same cases against a fresh pinned Linux build. Comparison output retains
all differences and must be reviewed; it does not silently accept mismatches.
`--build-linux NEW_ROOT` under WSL creates isolated pristine and current-port
builds, recording its build commands and the qpfit declaration-only exception.

Earlier audit `--verify` scripts, corrective probes, statistical oracles and
repair build commands below describe historical corrected-source experiments.
They can require removed APIs or assert intentionally changed upstream behavior;
do not run or count them as the current compatibility contract. Their source and
evidence are preserved for deferred upstream work, not part of the native build.


The [T01 qpAdm hard-check report](audits/T01_qpAdm.md) and its machine-readable
evidence record expand the original fixtures to qpAdm modes, all six genotype
formats, gzip, qpfstats, Windows paths/encoding, malformed inputs and sanitizer
reproductions. Run in a fresh directory:

```powershell
python tests/windows/audit_qpadm.py --bin bin --output validation-results/T01-windows
python tests/windows/audit_qpadm.py --verify validation-results/T01-windows
```

Use the same runner on pristine pinned Linux and on an isolated repaired Linux
build. `--select` takes a regex for focused checks; `--compare L W` retains raw
diffs and exit codes for review. An upstream crash or wrong result is not an
expected scientific result for a repaired case. Read the report's individual
exceptions rather than suppressing mismatched result lines or applying a numeric
tolerance. The native probes and their build instructions are also in that report.

The integration runner requires Python 3.10 or later and no Python packages.
It creates deterministic synthetic inputs; historical example logs are not used
as a numerical reference. Use a new output directory for each run.

## Native Windows

Build with the root PowerShell scripts, then run from the repository root:

```powershell
python tests/windows/parity.py --bin bin --output validation-results/windows
```

## Pristine Linux reference

Use a Linux installation or WSL with GCC, make, GSL and OpenBLAS development
packages. With Ubuntu, install `build-essential libgsl-dev libopenblas-dev
pkg-config`. On Linux, create an isolated checkout from the exact baseline:

```bash
git clone https://github.com/DReichLab/AdmixTools.git ~/admixtools-reference
cd ~/admixtools-reference
git checkout --detach 67bc219174a109951a9434e0a383ec464fb140ee
make -C src
make -C src rolloff rolloffp
make -C src diffmean LDLIBS=-lnick
```

Use sequential make for the pristine reference: upstream's parallel build can
race the creation of `libnick.a`. No Windows port source changes should enter the
reference build. The explicit `LDLIBS` places `libnick` before the scientific
libraries to work around upstream's `diffmean` link order. Point the same runner
at that source directory:

```bash
python3 /path/to/AdmixTools_Win/tests/windows/parity.py \
  --bin ~/admixtools-reference/src \
  --output /path/to/AdmixTools_Win/validation-results/linux
```

Record `gcc --version`, `pkg-config --modversion gsl openblas`, the source commit,
architecture and flags alongside the results. WSL outputs can be written directly
under the Windows checkout via `/mnt/c/...`.

## Compare

```powershell
python tests/windows/parity.py --compare validation-results/linux validation-results/windows
```

Success requires no missing executables, unexpected exits, stream differences,
data differences, or failed binary round trips. `comparison.json` and
`comparison.diff` retain the result; the comparison exits nonzero on failure.
The runner explicitly selects the executable path, so another installation on
PATH cannot substitute for the build being tested.

The allowed normalizations are implemented in `normalize()` and described in
`WINDOWS_PORT_STATUS.md`. Do not add tolerances or strip result lines to make a
test pass. All 18 generated files are compared byte-for-byte.

## Platform probes

`platform_probe.c` checks the Linux random stream, large integer rounding and
equal-key sorting. `largefile_probe.c` uses a sparse file just over 4 GiB to test
native file sizes, offsets, binary bytes and mapping after closing the descriptor.
It removes its test file on success. Use a filesystem supporting sparse files.

After building on Windows, compile using UCRT64 GCC (adjust the toolchain path):

```powershell
$toolchain = 'C:\msys64\ucrt64\bin'
$env:PATH = "$toolchain;$env:PATH"
& "$toolchain\gcc.exe" -std=gnu11 -Isrc -Isrc/nicksrc -include src/win32/compat.h tests/windows/platform_probe.c src/.windows/win32_compat.o src/.windows/libnick.a -lgsl -lopenblas -lz -lm -o bin/platform_probe.exe
& "$toolchain\gcc.exe" -std=gnu11 -Isrc -include src/win32/compat.h tests/windows/largefile_probe.c src/.windows/win32_compat.o -lz -o bin/largefile_probe.exe
.\bin\platform_probe.exe
.\bin\largefile_probe.exe validation-results/largefile.bin
```

For Linux, compile the platform probe with `-I/path/to/AdmixTools_Win/src/nicksrc`
and link the pristine reference's `src/nicksrc/libnick.a` with
`-lgsl -lopenblas -lm`. Compile `largefile_probe.c` normally with GCC.
`platform_probe rng` writes raw bytes; hash them without PowerShell text pipelines:

```powershell
python -c "import subprocess,hashlib; r=subprocess.run(['bin/platform_probe.exe','rng'],capture_output=True,check=True); print(len(r.stdout),hashlib.sha256(r.stdout).hexdigest())"
```

The expected length is 3,200,000 bytes and the reference SHA-256 is recorded in
`WINDOWS_PORT_STATUS.md`. These checks cover the platform layer; they do not
replace scientific integration tests for each executable.

## Main-thread stack

All Windows tool links use `-Wl,--stack,8388608` to match the tested Linux
reference's `ulimit -s` of 8192 KiB. The reserve is address space, committed as
needed. `stack_probe.c` touches 4 MiB of automatic storage, exceeding MinGW's
default 2 MiB reserve while remaining within that allowance:

```powershell
& "$toolchain\gcc.exe" -O2 '-Wl,--stack,8388608' tests/windows/stack_probe.c -o bin/stack_probe.exe
.\bin\stack_probe.exe
```

PowerShell interprets commas in unquoted arguments; if invoking GCC directly,
quote `'-Wl,--stack,8388608'`. The Python build runner passes it directly as one
argument. On Linux, use `gcc -O2 tests/windows/stack_probe.c -o stack_probe`.
Both should print `stack bytes: 4194304 checksum: 130560` and exit zero. Inspect
each installed executable with `objdump -p` to verify `SizeOfStackReserve` is
`0000000000800000`; testing the probe alone does not check the build links.

## Compressed input and native graph rendering

Build first, then use a fresh output directory. Add native Graphviz/Ghostscript
to the process PATH as described in `README.WINDOWS.md` for `--render`:

```powershell
python tests/windows/compatibility.py --bin bin --output validation-results/windows-compatibility --render
```

On Linux/WSL, point the same runner at the pristine pinned reference. Install
`graphviz ghostscript` for rendering, or omit `--render` on both platforms:

```bash
python3 /path/to/AdmixTools_Win/tests/windows/compatibility.py \
  --bin ~/admixtools-reference/src --output /path/to/AdmixTools_Win/validation-results/linux-compatibility --render
```

Compare on Windows:

```powershell
python tests/windows/compatibility.py --compare validation-results/linux-compatibility validation-results/windows-compatibility
```

This adds 11 shared cases when rendering is enabled. Compare all shared streams
and 14 genotype/graph/DOT files exactly. Only the documented metadata and the
generated gzip temporary pathname/command-operand quotation are normalized.
PDFs must be valid PDF 1.4 and parse successfully in Ghostscript; their bytes are
not compared across renderer versions/fonts. Both sides must run the same cases.
Raw files, output, dependency versions and comparison results are retained.
The runner removes only its verified decompressed Linux fixture files that
pristine upstream leaves under `/var/tmp/genotmp:PID` after early returns.

Windows additionally checks failed CRC/truncated/non-gzip/empty inputs, temporary
cleanup and paths with spaces/metacharacters. Fatal termination status is
required to be nonzero; no Unix signal-code equivalence is claimed.

## Installed Python helpers

```powershell
python tests/windows/script_helpers.py --bin bin --scripts bin/script --output validation-results/windows-script-helpers
```

On Linux, run that test file with `--bin ~/admixtools-reference/src` and
`--scripts ~/admixtools-reference/src/script`, using a separate Linux output
directory. Then compare:

```powershell
python tests/windows/script_helpers.py --compare validation-results/linux-script-helpers validation-results/windows-script-helpers
```

Twelve generated files must match byte-for-byte. The workflow checks conversion,
extraction, merge, sample ordering, hashes and temporary cleanup. Windows also
exercises parameter paths with spaces/metacharacters and forces the specific
denied-symlink error to verify the SNP copy fallback. This does not certify every
Perl/R/Python helper or byte-identical terminal output from all wrappers.

## T01 remaining-issue corrections

The [follow-up report](audits/T01_qpAdm.corrections.md) supersedes retained T01
CLI/EOF quirks and unbounded rejection sampling. `audit_qpadm.py` now verifies
version-only exits, accurate help, rejection of inactive parameters without
output creation, invalid limits, and the portable EOF diagnostic. Its full
scientific matrix remains applicable on Windows and isolated repaired Linux.
Compile `qpadm_probe.c` with `-DPROBE_SAMPLER` against qpAdm's dependencies to
force the rejection boundary; the report/evidence record modes and link commands.
Pristine Linux intentionally differs in these corrected cases.

## T02 qpfstats hard review

```powershell
python tests/windows/audit_qpfstats.py --bin bin --output validation-results/T02-windows
python tests/windows/audit_qpfstats.py --verify validation-results/T02-windows
python tests/windows/audit_qpfstats.py --compare validation-results/T02-linux validation-results/T02-windows
```

Run against the pinned pristine Linux reference and a separate repaired Linux
build, using a new output directory each time. The runner retains raw streams,
exits and scientific file hashes; `--select REGEX` limits diagnostic reruns.
Missing executables/timeouts are explicit failures. Compare scientific bytes
and printed precision exactly; examine the diff and raw exit statuses.
`--verify` checks completion, expected exits, owned temporary cleanup and
retention. The repaired helper lifecycle passes; pristine upstream is expected
to fail the new behavior assertions. Comparison retains intentional upstream
bug corrections rather than treating them as platform numerical differences.

The [initial T02 report](audits/T02_qpfstats.md) and
[corrections](audits/T02_qpfstats.corrections.md) record source/build controls,
consumer coverage and validation limits. `qpfstats_probe.c` exercises dimension
and list boundaries, actual sample selection, duplicate-name indices, and owned
temporary collision/cleanup/retention. Compile it against the real qpfstats
dependency objects (excluding `qpfstats.o`), libnick and scientific libraries on
both systems; pass `--probe PATH` to the runner to check physical-subset oracles.
Source inclusion is a test technique; production layout/link rules are retained.
The verbose case produces over three million lines; retain the complete streams
for comparison or use `--select '^(?!verbose$)'` for focused nonverbose reruns.

## T03 qpWave hard review

```powershell
python tests/windows/audit_qpwave.py --bin bin --output validation-results/T03-windows
python tests/windows/audit_qpwave.py --verify validation-results/T03-windows
python tests/windows/audit_qpwave.py --compare validation-results/T03-linux validation-results/T03-windows
```

Use separate new directories for pristine Linux, the Linux port and sanitizer
builds. `--select REGEX` restricts cases; `--probe PATH` accepts the existing
`qpfstats_probe` for independent physical-subset oracles. Without it, the two
manual-subset cases are omitted. All child processes have timeouts; stdout,
stderr, exit statuses, file hashes and temporary ownership are retained.
`--verify` checks the repaired safety/integrity behavior, including rejection of
inactive legacy controls and preservation of existing output files. Windows
BOM/quoted-space-path extensions are not required to succeed on Linux.
Comparisons return nonzero for any raw mismatch, including OS abort statuses;
inspect the classification rather than interpreting a nonzero comparison as a
floating-point mismatch. No scientific tolerances are used.

`qpwave_map_probe.c` includes the actual mapping implementation. On Linux,
compile with `-O2 -ffunction-sections -fdata-sections -Isrc -Isrc/nicksrc`, link
the real libnick and `-lm -Wl,--gc-sections`, then pass a new sparse-file path.
It limits only its own address space. Exit 10 detects the historical defect:
`constructMap` returned a failed mapping as a live object. Exit 9 means the
failure injection did not take effect; other statuses need inspection. It
returns 77 on Windows because this probe uses Linux `RLIMIT_AS`.

After correction, the real Linux mapping probe must terminate through the
`memory mapping failed` fatal path rather than returning 10. Define
`QPWAVE_FORCE_MAP_FAILURE` for a small Windows/Linux injected-failure probe.
On Windows, link the ordinary qpWave dependency objects except `qpWave.o` and
`mapfile.o`, plus libnick/compat/scientific libraries; the probe includes those
two sources to exercise the actual failure branch. `qpwave_probe.c` includes
the real dimension guard; link the ordinary dependency objects except
`qpWave.o`. Pass left/right dimensions to test the last supported and first
overflowing products without allocating their matrices.

See [T03 qpWave](audits/T03_qpWave.md) for initial findings, corrected fixture
definitions, exact comparison scope, architecture review and remaining limits.
The [T03 corrections](audits/T03_qpWave.corrections.md) supersede that initial
open status and document the fixed findings, current evidence and limits.

## T04 qpDstat and independent module review

The [T04 report](audits/T04_qpDstat.md) is **reviewed with open defects, not
passed**. Production behavior was not repaired. The 18 module reports and
[function inventory](audits/T04_modules.inventory.json) list remaining
contract/coverage gaps; none is a full-module certification.

The recorded four-build matrix has 146 cases; a later haploid/tree case is a
separate focused run. New complete invocations also include later parser/output
checks. Read actual counts/selections from each manifest.

Create an isolated snapshot/build on Windows using your actual UCRT64
toolchain. Output directories and Linux build trees must be new:

```powershell
$taskToolchain = 'C:\msys64\ucrt64\bin'
python tests/windows/build_t04_audit.py --output validation-results/hard-check/T04-new/builds --toolchain $taskToolchain
python tests/windows/build_t04_probes.py --tree validation-results/hard-check/T04-new/builds/snapshot --output validation-results/hard-check/T04-new/probes-windows --toolchain $taskToolchain
python tests/windows/audit_qpdstat.py --bin validation-results/hard-check/T04-new/builds/snapshot/bin --probe validation-results/hard-check/T04-new/probes-windows/module_probe.exe --output validation-results/hard-check/T04-new/windows
python tests/windows/audit_qpdstat.py --verify validation-results/hard-check/T04-new/windows
python tests/windows/audit_t04_modules.py --bin validation-results/hard-check/T04-new/builds/snapshot/bin --probes validation-results/hard-check/T04-new/probes-windows --output validation-results/hard-check/T04-new/modules-windows
python tests/windows/audit_t04_modules.py --verify validation-results/hard-check/T04-new/modules-windows
```

The toolchain path above is this audit's tested location; substitute your own.
The isolated build preserves the working checkout's `bin/`. Additional review
warnings from `inventory_t04_modules.py` are neither findings nor passes.

From the repo in WSL, use the snapshot output's actual Linux path:

```bash
python3 tests/windows/build_t04_audit.py --linux --output /mnt/c/path/to/repo/validation-results/hard-check/T04-new/builds
python3 tests/windows/build_t04_probes.py --tree "$HOME/admixtools-t04-linux" --output "$HOME/t04-new-probes/linux"
python3 tests/windows/audit_qpdstat.py --bin "$HOME/admixtools-t04-linux/src" --probe "$HOME/t04-new-probes/linux/module_probe" --output "$HOME/t04-new-results/linux"
python3 tests/windows/audit_qpdstat.py --compare "$HOME/t04-new-results/linux" /mnt/c/path/to/repo/validation-results/hard-check/T04-new/windows
```

Use Linux filesystem output for WSL matrices to avoid slow per-file Windows
mount I/O. The build refuses to overwrite its existing scratch trees; preserve
previous evidence and use `--linux-root NEW_DIRECTORY` for another build.
Repeat the runner/probe links for `admixtools-t04-pristine` and
`admixtools-t04-asan`; pass `--sanitizer` for sanitizer probes.
`--linux --coverage` creates a separate instrumented build; its probes require
`--coverage`. The original Linux reference is never patched.

`--select REGEX` limits diagnostic reruns. In PowerShell use `wsl -e python3`
when passing a regex, so another shell cannot interpret its parentheses/pipes.
Verifiers/comparators intentionally return nonzero for reproduced bugs, missing
executables, timeouts, raw OS status differences and stream/file mismatches.
Inspect the classification instead of loosening tolerances. Missing cases are
not silently excluded.

Run native checks with a new output directory:

```powershell
powershell -NoProfile -File tests/windows/t04_native_checks.ps1 -Bin validation-results/hard-check/T04-new/builds/snapshot/bin -Fixtures validation-results/hard-check/T04-new/windows/fixtures -Output validation-results/hard-check/T04-new/powershell
```

`collect_t04_evidence.py` collects the retained audit-specific paths after
validation, checks production hashes, and writes evidence/module reports.
Its Linux archive uses GNU sparse tar: extract it on a sparse-capable filesystem
so logical 4-GiB failure-probe fixtures are not expanded as ordinary byte streams.

### Requested T04 corrections

[The repair report](audits/T04_qpDstat.corrections.md) and
[machine evidence](audits/T04_qpDstat.corrections.evidence.json) supersede the
original open findings in their reproduced scopes. Behavior verifiers now pass
the repaired Windows/Linux/sanitizer matrices. Comparators continue returning
nonzero for retained raw OS statuses, paths, Windows input extensions and the
explicitly identified upstream defect corrections. Do not loosen tolerances.

Build into new directories, preserving the installed binaries and old reference:

```powershell
python tests/windows/build_t04_audit.py --output validation-results/hard-check/T04-repair-new/builds --toolchain C:/msys64/ucrt64/bin
wsl -e python3 tests/windows/build_t04_audit.py --linux --output validation-results/hard-check/T04-repair-new/builds --linux-root /home/user/t04-repair-new --skip-pristine
```

Adjust the toolchain and WSL paths to your machine. `--skip-pristine` uses the
retained pinned reference for later comparisons; it does not rebuild or modify it.
Repeat the probe/tool/module runner commands above for the new corrected native,
Linux and ASan trees. The current direct probes use the new bounded list API;
for a pristine probe rebuild use the original probe saved in the audit snapshot.
The current qpDstat runner can exercise pristine executables directly.

Run `verify_t04_repairs.py --help` for the required completed matrices, native
PowerShell record, shared qpWave runs, original native/pristine references and
build manifest paths. Run it under WSL so it can access both filesystems. It
requires a new output evidence filename, checks every behavior verifier and
source hash, compares scientific rows exactly against both corrected and pinned
references, and retains every raw terminal/file comparison. The original
`collect_t04_evidence.py` describes the pre-repair snapshot and must not be used
to replace the preserved original audit evidence with repaired-source results.

Authoritative repair artifacts use the `verified-*` names under
`validation-results/hard-check/T04/repairs/`; Linux raw inputs/streams/probes are
also retained in its separate sparse archive. The module/header queue remains
pending beyond the reproduced defects, and sibling probes are targeted checks.

### T05 qp3Pop

[The T05 report](audits/T05_qp3Pop.md) records open defects. Its independent
mixed-ploidy X and large-inbred-count oracles expose shared upstream scientific
failures; agreement between native/Linux outputs is not a pass. Production
sources and the installed binaries were not changed by this audit.

Use new scratch paths (substitute your compiler and WSL mount paths):

```powershell
python tests/windows/build_t05_audit.py --output validation-results/hard-check/T05-new/builds --toolchain C:/msys64/ucrt64/bin
wsl -e python3 /mnt/c/path/to/repo/tests/windows/build_t05_audit.py --linux --output /mnt/c/path/to/repo/validation-results/hard-check/T05-new/builds --linux-root /home/user/t05-new
python tests/windows/build_t05_probe.py --tree validation-results/hard-check/T05-new/builds/snapshot --output validation-results/hard-check/T05-new/probes --toolchain C:/msys64/ucrt64/bin
python tests/windows/audit_qp3pop.py --bin validation-results/hard-check/T05-new/builds/snapshot/bin --probe validation-results/hard-check/T05-new/probes/qp3pop_probe.exe --output validation-results/hard-check/T05-new/complete-windows
```

Build the probe against each Linux source tree, passing `--sanitizer` for ASan,
then run `audit_qp3pop.py` against each tree's `src/` binary directory and its
matching probe. The pristine probe must include the pristine tree's qp3Pop.c.
Use Linux filesystem output to avoid per-file Windows mount overhead. A separate
`build_t05_audit.py --linux --coverage` invocation builds the coverage tree;
its probe needs `--coverage`. `build_t05_probe.py --sanitizer --float-cast`
also recompiles qpsubs.c with the explicit floating-to-integer overflow check.
It leaves the production executable/object unchanged.

```powershell
python tests/windows/audit_qp3pop.py --verify validation-results/hard-check/T05-new/complete-windows
wsl -e python3 /mnt/c/path/to/repo/tests/windows/audit_qp3pop.py --compare /home/user/t05-new/complete-linux /mnt/c/path/to/repo/validation-results/hard-check/T05-new/complete-windows
powershell -NoProfile -File tests/windows/t05_native_checks.ps1 -Binary validation-results/hard-check/T05-new/builds/snapshot/bin/qp3Pop.exe -Fixture validation-results/hard-check/T05-new/complete-windows/fixtures -Output validation-results/hard-check/T05-new/native-powershell-final
```

The verifier/comparator returns nonzero while recorded defects/raw differences
remain. Collection itself can complete successfully while preserving failures;
inspect `verification.json`, scientific rows, original streams and case statuses.
Never replace missing output or widen numeric tolerances to obtain a pass.

The separate shared-module runner can use T04's production-function probe
builders and this selection (quoted as one argument):
`^(?!M13-map-failure|caller-(qpAdm|qpfstats|qpWave|qpdslow|qpDpart)|T04-)`.
Pass `--skip-map` to `build_t04_probes.py` for this selection: the T05 tool set
excludes rank/eigen objects needed by the unused Windows qpWave injection job.
The module/platform/largefile/argv probe executables build normally. The new
flag leaves the helper's default T04 behavior unchanged. Use a broader isolated
tool build to rerun the excluded injection job.

`collect_t05_evidence.py --help` describes its explicit Windows/Linux scratch
paths. It requires completed `complete-*`, shared-module and native matrices,
the recorded Windows package versions in `windows-environment.txt`, and the
matching `probes-final-*`/`probes-float-*` trees. It runs focused leakage,
float-cast, zero-denominator and `/dev/full` probes, checks source hashes, and
collects coverage plus raw comparisons. The checked-in report/evidence identify
the exact retained paths; this collector is an audit helper, not an installer.

Authoritative Windows results are under `validation-results/hard-check/T05/`;
Linux raw results/probe build records are also retained in
`linux-artifacts.tar.gz` there. Extract using GNU sparse support on a
sparse-capable filesystem: module offset probes contain logical files beyond
4 GiB. Earlier diagnostic matrices remain historical, not replacement evidence.

### T05 corrections

[The repair report](audits/T05_qp3Pop.corrections.md) closes the 14 recorded
finding groups in their tested scopes. The original report/hashes/failing
streams and original harness bytes are retained. New runs against corrected
sources must use `audit_qp3pop.py --repairs`; the earlier commands above describe
the original audit contract and will continue to flag its intentional repairs.

Use fresh paths and build affected consumers:

```powershell
python tests/windows/build_t05_audit.py --related --output validation-results/hard-check/T05-repair-new/builds --toolchain C:/msys64/ucrt64/bin
wsl -e python3 /mnt/c/path/to/repo/tests/windows/build_t05_audit.py --linux --related --skip-pristine --output /mnt/c/path/to/repo/validation-results/hard-check/T05-repair-new/builds --linux-root /home/user/t05-repair-new
python tests/windows/build_t05_probe.py --tree validation-results/hard-check/T05-repair-new/builds/snapshot --output validation-results/hard-check/T05-repair-new/probes-verified-windows --toolchain C:/msys64/ucrt64/bin
python tests/windows/audit_qp3pop.py --repairs --bin validation-results/hard-check/T05-repair-new/builds/snapshot/bin --probe validation-results/hard-check/T05-repair-new/probes-verified-windows/qp3pop_probe.exe --output validation-results/hard-check/T05-repair-new/verified-windows
```

`--skip-pristine` retains the pinned original reference; the broader pristine
qpfit build has its documented declaration conflict and must not be patched to
make it appear pristine. Repeat probe links and the repair matrix for Linux and
ASan; pass `--sanitizer --float-cast` for the sanitizer probe. Their source
hashes are now recorded at link time. `--related` supplies the rank/eigen
objects for the normal full shared-probe builder, including map-failure probes.

Run `verify_t05_repairs.py --help` under WSL for the Windows/Linux root paths and
new output filename. It requires the completed `verified-*`, modules,
qpAdm/qpfstats/qpWave/qpDstat, native and installed check directories recorded in
the correction evidence. It checks expected matrix counts, behavior verifiers,
exact scientific rows, narrow original/pristine differences, source/build and
installed provenance, native broken-pipe output errors, `/dev/full` and a
LeakSanitizer-enabled low-data probe. Its own failure list must be empty.
Comparators still retain raw OS statuses and paths; they are not full-stream
parity certificates.

Corrected raw Linux builds/results are in the separate sparse archive under
`validation-results/hard-check/T05/repairs/`. The installed bin was rebuilt only
after the scoped checks passed; its previous bytes/hashes are backed up in
`repairs/installed-before/`. Full-suite parity, macOS runtime and independent
module/header audits remain incomplete.

### T06 qpF4ratio

[T06](audits/T06_qpF4ratio.md) is **reviewed with open defects**. The connected
module report and evidence distinguish exact platform agreement from correctness:
131 cases per build, 15/19 independent oracle cases passing, four X oracle
failures, nine inherited finding groups open and a corrected Windows CLI
diagnostic. Existing `bin/` was not replaced. Never treat the runner completing
as a pass: `--verify` deliberately returns nonzero while findings remain.

Create new output directories; the commands below do not overwrite prior
evidence. From the project root in PowerShell:

```powershell
$taskToolchain = 'C:/msys64/ucrt64/bin'
python tests/windows/build_t06_audit.py --output validation-results/hard-check/T06-new/builds --toolchain $taskToolchain
wsl -e python3 tests/windows/build_t06_audit.py --linux --output validation-results/hard-check/T06-new/builds --linux-root /home/user/t06-new
wsl -e python3 tests/windows/build_t06_audit.py --linux --coverage --output validation-results/hard-check/T06-new/builds --linux-root /home/user/t06-new
python tests/windows/audit_qpf4ratio.py --bin validation-results/hard-check/T06-new/builds/snapshot/bin --output validation-results/hard-check/T06-new/final-windows
wsl -e python3 tests/windows/audit_qpf4ratio.py --bin /home/user/t06-new/pristine/src --output /home/user/t06-new/final-pristine
wsl -e python3 tests/windows/audit_qpf4ratio.py --bin /home/user/t06-new/linux/src --output /home/user/t06-new/final-linux
wsl -e python3 tests/windows/audit_qpf4ratio.py --bin /home/user/t06-new/asan/src --output /home/user/t06-new/final-asan
wsl -e python3 tests/windows/audit_qpf4ratio.py --bin /home/user/t06-new/coverage/src --output /home/user/t06-new/final-coverage
python tests/windows/audit_qpf4ratio.py --verify validation-results/hard-check/T06-new/final-windows
wsl -e python3 tests/windows/audit_qpf4ratio.py --compare /home/user/t06-new/final-linux validation-results/hard-check/T06-new/final-windows
```

Comparators retain raw OS exit codes, absolute data paths, Windows input
extensions, nonfinite signs and sanitizer diagnostics. A nonzero comparator
status must be investigated using its JSON/diff, not dismissed as a numerical
tolerance issue. Every result row and printed number is compared.

Direct function checks and native PowerShell checks:

```powershell
python tests/windows/build_t06_probe.py --tree validation-results/hard-check/T06-new/builds/snapshot --output validation-results/hard-check/T06-new/probes-windows --toolchain $taskToolchain
python tests/windows/run_t06_probes.py --binary validation-results/hard-check/T06-new/probes-windows/qpf4ratio_probe.exe --output validation-results/hard-check/T06-new/direct-windows
wsl -e python3 tests/windows/build_t06_probe.py --tree /home/user/t06-new/linux --output /home/user/t06-new/probes-linux
wsl -e python3 tests/windows/build_t06_probe.py --tree /home/user/t06-new/asan --sanitizer --output /home/user/t06-new/probes-asan
wsl -e python3 tests/windows/run_t06_probes.py --binary /home/user/t06-new/probes-linux/qpf4ratio_probe --output /home/user/t06-new/direct-linux
wsl -e python3 tests/windows/run_t06_probes.py --binary /home/user/t06-new/probes-asan/qpf4ratio_probe --output /home/user/t06-new/direct-asan
powershell -NoProfile -File tests/windows/t06_native_checks.ps1 -Binary validation-results/hard-check/T06-new/builds/snapshot/bin/qpF4ratio.exe -Fixture validation-results/hard-check/T06-new/final-windows/fixtures -Output validation-results/hard-check/T06-new/native-powershell-final
```

The direct sanitizer runner enables LeakSanitizer and repeats ratio/diff
allocations 16 times. Native tests require one actual result row, equal Tee/gzip
results, empty stderr, successful exits, backslash temporary paths and cleanup.

For shared probes, reuse `build_t04_probes.py --skip-map`, with the appropriate
tree/toolchain/`--sanitizer` flags, then `audit_t04_modules.py --select
'^(?!M13-map-failure)(M|caller-(?:qp3Pop|qp4diff|qpF4ratio|transpose))'` and its
`--verify`. This produces 80 native and 78 Unix cases. The qpWave-specific
map-failure injection is excluded because this isolated tool set has no rank
objects. The inventory generator can include T06 by adding `T06` to its `IDS`
list at invocation; the checked-in inventory records the actual compiler scan.

`collect_t06_evidence.py --help` describes the Windows/Linux/shared root paths.
It checks completed manifests and production hashes, retains both streams and
all statuses, evaluates scientific agreement separately, and reruns qpF4ratio
alone with a fresh `GCOV_PREFIX`. It also requires the retained pre-fix
`original-windows` and post-fix `windows` diagnostic matrices to document the
CLI-only correction. These historical matrices are already retained for T06;
they cannot be substituted with an unknown installed binary. The aggregate
coverage matrix and isolated tool counters are separate.

Authoritative native runs: `validation-results/hard-check/T06/final-windows`.
Linux: `/home/user/admixtools-t06-final/final-{pristine,linux,asan}`; shared and
coverage: `/home/user/admixtools-t06/`. The machine evidence records a portable
Linux raw-input/stream/executable archive and SHA-256. Earlier interrupted
`complete-*` directories are not completed evidence. Independent M/H/Q checks,
X format equivalence, macOS, real giant genotypes and research datasets remain
uncompleted.

### T06 corrections

**Historical, deferred upstream-bug experiment.** After the user's scope
clarification, its production changes were removed. The commands below target
the retained experimental builds, not current source or installed binaries.
Current work addresses Windows porting differences; inherited Linux behavior
is retained. See [scope restoration](audits/T06_scope_restoration.md).

The original T06 review and 131-case evidence remain historical. Current repairs
use `audit_qpf4ratio.py --repairs --probe PATH`; the seeded physical-subset checks
require the production-function probe. This matrix has 225 cases and 50 independent
oracle cases. Use the same Windows/Linux commands above with `--repairs`, fresh
output directories and corrected probes. `run_t06_probes.py` now has 11 cases.

`build_t06_audit.py --related` includes affected qpAdm/qpfstats/qpWave/qpfit/qpdslow
links. `--skip-pristine` retains the original pristine build rather than attempting
to overwrite it. Explicit `--linux-root` is required. The managed environment may
require approved WSL command execution; all repair outputs can remain below the
project's validation-results directory.

`verify_t06_corrections.py --root validation-results/hard-check/T06/repairs
--output NEW_JSON` runs under WSL after completed-windows/linux/asan matrices,
direct probes, shared matrices, qpDstat and selected rank/precomputation consumers,
native and installed checks finish. It enforces all matrix/oracle case counts,
retains exact scientific comparisons and permits only the named intentional
seed/X/version differences against the original/pristine records. Its failure
list must be empty before closing a finding. See
[the correction report](audits/T06_qpF4ratio.corrections.md) for authoritative
paths, scope and remaining independent coverage limits.

# Reproducing Linux/Windows comparisons

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

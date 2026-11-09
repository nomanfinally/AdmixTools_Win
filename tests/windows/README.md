# Reproducing Linux/Windows comparisons

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

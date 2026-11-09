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
& "$toolchain\gcc.exe" -std=gnu11 -Isrc -Isrc/nicksrc -include src/win32/compat.h tests/windows/platform_probe.c src/.windows/win32_compat.o src/.windows/libnick.a -lgsl -lopenblas -lm -o bin/platform_probe.exe
& "$toolchain\gcc.exe" -std=gnu11 -Isrc -include src/win32/compat.h tests/windows/largefile_probe.c src/.windows/win32_compat.o -o bin/largefile_probe.exe
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

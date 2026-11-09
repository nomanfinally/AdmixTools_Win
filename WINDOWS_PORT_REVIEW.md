# Review of the local Sapphiregnm Windows port

Reviewed on 10 November 2026 to learn Windows compatibility methods while
preserving upstream calculations, terminal output, and repository layout.

## Sources and scope

- Reference checkout: `C:\work\reference-port`.
- Reference HEAD: `eb0c20235aa642b96f7d43ecfbebe803aead6a83`, from
  Sapphiregnm / sapphire-xyz's `AdmixTools_Windows` repository.
- Our upstream baseline: `67bc219174a109951a9434e0a383ec464fb140ee`.
- Compared all 112 C/header files shared with that baseline after normalizing
  CRLF to LF: 50 differ and 62 are unchanged. Reviewed the changed hunks, all
  seven added C/header files, the batch build, license notices and setup guides.
  Both `src/Makefile` and `src/nicksrc/Makefile` match upstream unchanged.
- `WINDOWS_SETUP_BEGINNER.md` is untracked in the reference checkout; it was
  read as local documentation, not treated as part of the pinned commit.
- The other checkout was left unchanged. Its prebuilt executables were not used
  as a numerical reference or copied into our build.

The local `LICENSE`, section 1, attributes the Windows additions to Sapphiregnm
and declares GPL-3.0-or-later terms; it also lists separate upstream/dependency
notices. This review records techniques and source locations. No implementation
or tutorial text was copied from that checkout in this change. Any future source
reuse must retain the applicable notices and attribution. Existing dependency
license handling remains in our build scripts.

The detailed source diff, file hashes and inventory are saved locally in
`validation-results/reference-port-review/{source.diff,manifest.json}`. The
decisions below are maintained in this tracked document so they survive cleaning
generated validation artifacts. Reference paths below are relative to the other
checkout; our implementation paths are relative to this repository.

## Compatibility methods and decisions

| Method | Reference implementation | Our treatment |
| --- | --- | --- |
| Native toolchain | `build_windows.bat`: MSYS2 UCRT64 GCC, GSL, OpenBLAS | Already use that toolchain. Select its explicit path, isolate objects in `src/.windows`, and retain upstream target dependencies. PowerShell/Python argument arrays also support build paths containing spaces. |
| LAPACK ABI | `src/eigx.c`: Fortran declarations with 32-bit integers | Already handled for MinGW. Keep Apple and other Unix branches intact; do not infer the BLAS integer ABI from pointer width. |
| Wide sizes and offsets | `packit.h`, `mcio.[ch]`, `h2d.c`, `snpunion.c`, `tmcio.h`: widen packed lengths | Already use `admix_long` / `admix_ulong` to preserve Linux LP64 signedness and widths on Windows LLP64. Also use 64-bit stat/seek and matching print/scan formats. Avoid changing signed sentinels to unsigned as a blanket fix. |
| Wide hashes and modular arithmetic | `easycheck.c`, `nicksrc/vsubs.[ch]`, `nicksrc/xsearch.[ch]`: 64-bit hash intermediates and split values | Already covered by shared width aliases, including callers and declarations. Preserve upstream's hash operations; the reference also changes signed shift behavior, which is a separate algorithm change. |
| 64-bit math branch | `nicksrc/statsubs.c`, `mcio.c`: use pointer width instead of Windows `sizeof(long)` | Already select the upstream 64-bit branch using the LP64-equivalent type. Preserve scientific code and size checks. |
| Binary CRT I/O | `admutils.h`: add `O_BINARY` to `open`; dispatcher: `_set_fmode(_O_BINARY)` | Already set binary defaults and stdin/stdout/stderr modes in every executable's shared constructor. Covers the small tools too, preserving LF bytes and Ctrl-Z payloads. |
| POSIX memory mapping | Added `src/sys/mman.h`: Windows mapping objects and views, close mapping handle, unmap view | Already implement the upstream-used read-only, private, offset-zero cases in `src/win32/mman.h`, with explicit rejection of unsupported modes and errno values. Do not broaden the interface for unused writable/anonymous modes. The view survives closing the file descriptor. |
| Missing `getline` | `nicksrc/strsubs.c` and added `argp.h`: grow a byte buffer with realloc | Already provide one shared implementation rather than duplicate definitions. Preserve line bytes and EOF behavior. |
| Missing `setenv` | `admutils.h`: `_putenv_s` wrapper | Already honor `overwrite`, validate names, and update both the CRT and Win32 environment so helper processes inherit changes. The reference ignores `overwrite`. |
| Directory creation | `admutils.c`: one-argument Windows mkdir | Already adapt the signature centrally in `src/win32/compat.h`. The upstream directory-existence/error path still needs attention for compressed inputs; see gaps below. |
| Linux-only headers/services | `nicksrc/strsubs.c`: guard `sys/times.h`, `sys/prctl.h`, errno redeclaration and `prctl` | Already guard platform APIs; retain `prctl` only on Linux so macOS is also supported. Use native CPU accounting; Windows `clock()` is not a substitute for Linux process CPU time. |
| Automatic seeds | `nicksrc/strsubs.c`: PID/time/clock fallback | Already use native time/PID inputs. Automatically chosen seeds can differ by run; an explicit seed must reproduce the Linux random stream. |
| Temporary paths | `nicksrc/strsubs.c`: STMP, otherwise TEMP/TMP/current directory; numerous tools change `trashdir` to `.` | Already use STMP or `GetTempPathA`, sanitize generated filename colons, and print native backslashes. Do not change every scientific tool's globals. The repeated `trashdir` edits alone do not repair compressed input. |
| Linux random stream | `nicksrc/gauss.c`, `ranmath.h`: TYPE-3 additive generator | Already have a separate platform implementation tested against glibc, including zero and high unsigned seeds. Keep it out of scientific source files and preserve the default seed. |
| Heap diagnostics | `nicksrc/vsubs.c`: replace unavailable `sbrk(0)` with NULL | Already use native memory accounting for diagnostics. Returning NULL cannot provide meaningful heap deltas. Only memory measurements may vary. |
| Shell-free parameter filtering | `admutils.h`, `qpAdm.c`, `qpWave.c`, `qpfit.c`, `qpmix.c`, `qpGraph.c`: replace two `fgrep -v` commands with C filtering | Already share an implementation using dynamically sized lines and checked I/O, preserving the exact substring exclusion rules. |
| Shell-free file copying | `admutils.h`, helper call sites: binary stream copy instead of `cp` | Already use native file copying. Cover graph output/log copies as well as qpAdm/qpWave helper output. |
| Native helper processes | `admutils.h`: find executable directory, quote arguments, redirect log handles, `CreateProcessA`, wait and collect exit code | Already resolve the exact sibling executable, apply CRT argument quoting including trailing backslashes/quotes, and preserve upstream stderr routing. Do not fall back to another installation on PATH or merge stderr into the helper stdout log. `kimf` also uses the sibling `qpreroot`. |
| Failed helper output | `qpAdm.c`, `qpWave.c`: avoid fclose on a failed open | Already guarded for Windows across the relevant helper call sites. Do not import extra failure banners or a replay of the helper log into stdout. |
| GNU argp replacement | Added `src/argp.h`: reduced parser sufficient for some successful commands | Use actual pinned GNU argp instead. The reduced parser skips unknown options and changes help, errors, formatting, callbacks and exit behavior. Our help and invalid-option cases are compared against Linux. |
| Main-thread stack reserve | `build_windows.bat`: `--stack,67108864` (64 MiB) | **Added here:** use 8 MiB, matching this Linux reference's observed 8192 KiB allowance, instead of MinGW's 2 MiB default. Record the link flag in `windows-build.json`. This changes the execution allowance, not calculation order or optimization. |
| Static runtime packaging | `build_windows.bat`: static linking and libgcc/Fortran/quadmath flags | Static linking is a packaging option, not required for a native port. Retain our checked DLL dependency closure beside each executable and dependency notices. Do not mix UCRT/MSYS libraries or assume an exe has no external imports. |
| UTF-8 console selection | Added dispatcher: `SetConsoleOutputCP(CP_UTF8)` | Defer pending a deliberate Unicode I/O/path policy and tests. Changing the console code page alone does not make `CreateFileA`, `fopen` or argv paths Unicode-safe. Avoid altering the user's console state as an incidental dispatcher feature. |
| Beginner setup | Local setup guides: prerequisites, build, working directory, PATH, parameters, logs and upgrade/removal | Already covered in `README.WINDOWS.md` for our separate executables. Preserve process-local compiler PATH changes, explain how to identify the executable being launched, and avoid examples that silently select the other port. |

## Changes excluded from an analogous port

These exclusions follow from the observed source and our current upstream
baseline; they are not a judgment about the other project's different goals.

- **Changed scientific defaults:** the reference changes `oasmode` from YES to
  NO in both `qpAdm.c` and `qpWave.c`, conditionally suppresses the oracle-mode
  line, and moves `yscale` into shared globals. `admixtools_globals.c` also
  replaces tool-specific global initializers and resets. Keep the current
  upstream defaults and per-tool globals.
- **Genotype-loading optimization:** `mcio.c` replaces packed genotype reads
  with writable-copy memory mapping and changes read chunking/progress output.
  This is distinct from implementing mmap where upstream already uses it.
- **Allocation/loop optimizations:** `qpsubs.c` caches a persistent per-SNP
  workspace; `admutils.c` compresses `rbuff`; `nicksrc/vsubs.c` replaces a loop
  with memset. Retain upstream implementations during compatibility work.
- **Merge redesign:** `mergeit.c` adds OpenMP, a new packing loop, SNP reference
  selection, allele harmonization, new options/defaults, different missing-data
  handling and logging. Its `VirtualQuery`/unmapping cleanup belongs to its new
  mapped-loading design and is unnecessary with our upstream allocation path.
- **Compiler changes:** do not import uniform `-O3`, `-mpopcnt`, `-fopenmp`,
  `--allow-multiple-definition`, symbol rewriting or shared engine archives.
  Keep upstream's existing per-library optimization levels and separate links.
  Retain `-ffp-contract=off`; that flag alone is not evidence of parity.
- **Combined executable and logging:** omit `admixtools_dispatcher.c`,
  `adm_logger.[ch]`, symbol isolation, new banners/help, automatic logs and
  progress updates. Keep upstream CLI and stdout/stderr behavior.
- **Hash/validation changes:** unsigned rotation in `xcshift` changes the result
  for negative inputs. Changes to header initialization, parsing and conditional
  hash checks in `mcio.c`, and new `hashcheck` parameters in several tools, need
  separate upstream bug-fix review and malformed-input fixtures. Do not import
  them as Windows API substitutions.
- **Guessed statistical repair:** the reference changes `qpfmvmix`'s `b=q` to
  `b=a` and `pops[ab ;` to `pops[b]`. These repair compilation by choosing intended
  calculations without a working upstream reference. Keep our explicit blocked
  target until the intended algorithm is established separately.
- **General cleanups:** new null-pointer guards, the missing `dirname` argument
  in `makedir`'s error diagnostic, header guards and `kimf`'s `printpars` call
  cleanup are not evidence that statistical changes are needed to port Windows.
  Review genuine upstream defects separately rather than copy a mixed patch.
- **Parity claims and demo tests:** documentation and `test_eig.c` do not replace
  a recorded Linux/Windows comparison. The latter only prints one eigensystem;
  it does not assert a reference answer or certify the suite.

## Gaps revealed by the review

At the time of the review, direct `.geno.gz` loading was incomplete. The next
compatibility pass added native zlib decompression and tested all four genotype
representations plus `qpreroot` rendering and the Python helper workflow. See
`WINDOWS_PORT_STATUS.md` for the current evidence and remaining failure cases.

The original gap was: upstream
`mcio.c:getgenos` uses `trashdir`, a `genotmp:PID` name, unquoted `gunzip` shell
commands, and a directory helper whose Windows existence behavior needs repair.
The reference changes the default directory but retains the colon name and shell
path. A complete solution needs native temporary names, safe decompression
invocation, cleanup, and compressed-versus-uncompressed Linux comparisons.
The review itself made no gzip/format changes; the subsequent pass reuses the
original genotype readers after native decompression.

Optional graph rendering and other interpreter/external-command paths remain
separate validation work. Unicode/long-path support also remains unverified.
The reference's ANSI Win32 calls and console-code-page change do not close those
gaps. See `WINDOWS_PORT_STATUS.md` for the remaining scientific fixtures.

## Verification of this change

- Rebuilt all 37 supported separate Windows tools; inspected all 37 PE headers:
  stack reserve `8388608`, initial commitment `4096` bytes.
- The new `tests/windows/stack_probe.c` touches 4 MiB of automatic storage.
  With the old default reserve it exits with Windows stack overflow
  `0xc00000fd`; with the 8 MiB reserve it exits zero and prints
  `stack bytes: 4194304 checksum: 130560`. The same probe passes on Linux.
  This demonstrates the execution-limit difference, not a failure observed in
  an actual scientific fixture.
- Ran all 35 existing cases across 26 executables against the pristine pinned
  Linux reference: 70 stdout/stderr comparisons and 18 generated-file comparisons
  match, with expected exits and exact binary round trips. Scientific text and
  files use exact comparison; only previously documented metadata is normalized.
- Results: `validation-results/windows-port-review/comparison.json` and
  `validation-results/reference-port-review/{stack-results.json,executable-stacks.json}`.
  Reproduction commands are in `tests/windows/README.md`.

These results cover the listed fixtures. They do not certify every tool/input or
the unimplemented compressed-input path. No new performance optimization,
statistical default, calculation, repository restructuring or automatic logging
was introduced by this review.

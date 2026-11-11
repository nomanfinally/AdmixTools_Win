# T01 — qpAdm

Scope notice (11 November 2026): this is historical audit evidence.
Inherited-bug repairs described here are not the current porting baseline.
See [the project-wide restoration](PORT_ONLY_SCOPE_RESTORATION.md) for
active sources, retained Windows adaptations and new reference results.

Follow-up: the requested [remaining-issue corrections](T01_qpAdm.corrections.md)
supersede F024/F025 and the unbounded-sampler limitation below. The original
report and evidence remain a record of the initial audit. Current follow-up
source hashes and validation are recorded separately. Coverage limitations
remain; the status is still **passed with limitations**.

Status: **passed with limitations**, 10 November 2026, for the recorded
Windows/Linux matrix. This report distinguishes the pinned upstream
behavior from deliberate repairs to broken cases. It is not a full-suite parity
certificate. Related M/H/T items retain their own audit status.

Reference: `67bc219174a109951a9434e0a383ec464fb140ee` (package 8.1.0,
qpAdm 2206). Working base: `a8e87433a8e63008d0163314e84802538219d5c4` plus
the uncommitted changes recorded in `T01_qpAdm.evidence.json`.
Raw inputs, stdout, stderr, exits, binaries and diffs are retained locally under
`validation-results/hard-check/T01/`; they contain synthetic data.

## Contract and execution paths

The executable remains `qpAdm.exe`, version `2206.w`. It accepts the upstream
`-p`, `-h`, `-v`, `-V`, and `-d` switches. Source and documentation reviewed:
`src/qpAdm.c`, `README.qpWave`, `README.qpfstats`, `convertf/README`, the direct
link inputs in the inventory, and the Windows changes relative to the reference.

| Path | Functions/modules examined and exercised |
| --- | --- |
| CLI and parameters | `readcommands`, getopt, `openpars/readpars`, includes/substitution, string/integer/double readers, parameter echo; M03 and H contracts |
| Genotype input | `getsnps`, `getindivs`, `getgenos`, packed/TGENO readers, PED/BED suffix dispatch, gzip; M11–M14, M18, shared hashing |
| Ordinary fitting | counts, population selection, chromosome/position filters, block construction, `doq4vecb`, jackknife, covariance, rank fits, fixed-source patterns and worst-right-mixture diagnostics; M17–M23 and libnick |
| All-SNP fitting | `mkfstats` → sibling `qpfstats` → `fstats2popl/loadfstatsx/loadymv/geteffblocks` → bootstrap; T02, M01, M17, M24, input modules and libnick |
| Cached fstats | Same covariance/rank/bootstrap path without genotype files or a child process |
| Bayesian fitting | `newmode`/`oldmode`, importance sampling in `mcest/phiint`, positive-coefficient rejection, Gaussian RNG and matrix solvers |
| Output variants | details, high-resolution and high-precision covariance, eigenanalysis, diagonal-only covariance, long summaries, ratios, `mvname`, saved fstats and helper log |
| Platform services | binary CRT I/O, owned temporary files, sibling lookup/CRT argument quoting, environment, Unicode process code page, stat/seek/mapping and LP64-equivalent result integers |

Default statistical behavior remains upstream: oracle/OAS enabled, oldmode
enabled, details enabled, allsnps unset resolves to NO, inbreed unset follows
allsnps, 1,000 bootstrap draws when used, and upstream seed selection when no
explicit seed is supplied. No algorithm, RNG, floating-point tolerance, SIMD,
parallelism or optimization setting was introduced.

All parsed keys were traced, including aliases (`useallsnps`, `oasmode/oracle`,
`output/outputname`) and legacy keys. `maxrank` is overwritten by qpAdm's
codimension-one/full-rank workflow. `output/outputname` opens an otherwise unused
file; stdout is the result. These inherited behaviors are documented rather than
inventing new semantics. `diagplus` is used inside f4rank when oracle is off;
it is intentionally ignored in oracle mode, as upstream documents. The old
`oldallsnpsmode` branch is not reachable through the parsed parameters here.
PROB likelihood input is not called by qpAdm/qpfstats and is outside T01.

## Build and comparison controls

- Windows: native x86-64 UCRT64 GCC 16.2.0, GSL 2.8, OpenBLAS 0.3.34,
  zlib 1.4. `build-windows.ps1` builds all 37 supported executables. Existing
  application `-O2` and libnick `-O3` remain; `-ffp-contract=off`,
  `-fno-fast-math`, 64-bit file offsets and an 8 MiB stack remain enabled.
- Pristine Linux: isolated WSL Ubuntu x86-64, GCC 15.2.0, GSL 2.8,
  OpenBLAS 0.3.32; original sources at the exact reference commit. Separate
  builds of the repaired Linux sources establish cross-platform agreement for
  upstream bug fixes. The user's `/home/user/AdmixTools` checkout is unchanged.
- Sanitizers: isolated Linux builds with AddressSanitizer and UndefinedBehaviorSanitizer,
  debug information, frame pointers and non-PIE executables. Leak detection is
  disabled: this audit checks invalid accesses/UB, not a claim that upstream
  frees every process-lifetime allocation. Windows itself was not ASan-instrumented.
- `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`,
  `OPENBLAS_CORETYPE=NEHALEM`, `LC_ALL=C`; seed 77 plus a high-bit seed case.
  Fixtures include both weakly informative data and an informative 60/40 mixture
  (the latter actually reaches the Bayesian sampler).
- Scientific text is compared exactly at printed precision; generated `.mv`,
  fstats and genotype files are compared by bytes. No numerical tolerance.

Allowed metadata normalizations are explicitly implemented in the runner:
CRLF/LF; binary path/`.exe`; the requested `.w` suffix; CPU time and memory;
mapped addresses; generated temporary names/PIDs and path separators; gzip
command operand quotes. An auto-seed value is normalized **only** for CLI `-v`
without parameters. Explicit seeds and scientific/result lines are not removed.

Native abort exits differ (`SIGABRT` on Linux versus the Windows CRT termination
code); returning `-1` is observed as 255 versus 4294967295. Raw values are kept.
The Linux shell adds `Aborted` after a failed qpfstats child; Windows invokes the
child directly. Windows also accepts UTF-8 BOM parameters and diagnoses malformed
Windows quoting earlier. These are recorded differences, not numerical parity.

## Recorded final evidence

The executable/source hashes, environment, raw exit statuses and case names are
in [T01_qpAdm.evidence.json](T01_qpAdm.evidence.json).

| Check | Actual final observation |
| --- | --- |
| Windows mode/error/format matrix | 129 checks; all repaired-contract assertions pass |
| Repaired Linux matrix | 125 checks; all assertions pass |
| ASan + UBSan matrix | 125 checks; no invalid-access/UB reports; expected fatal inputs remain failures |
| Shared repaired Linux/Windows cases | 121 cases; all 81 jointly successful cases match both streams exactly after the listed metadata normalization |
| All shared streams, including failures | 236 of 242 exact; six differences occur only in four documented non-scientific/error cases: failed-child shell text, BOM acceptance, zero-errno perror wording, and Windows quote diagnostics |
| Fixture/data files | 17 common genotype/SNP/individual/fstats files and two model outputs match by bytes |
| Pristine suite regression | 35 cases across 26 tools; all 70 streams and 18 generated files exact; binary round trip exact |
| Additional shared regressions | 10 gzip/conversion cases and 12 generated data files exact; installed Python helper workflow's 12 files exact |
| Integer/hash/RNG/offset/stack | 1,533 shared hashes exact; 800,000 RNG outputs exact; tie rounding and stable sorts retained; sparse 4 GiB size/seek/mmap and 4 MiB stack-touch probes pass |
| Block boundary | Pristine 1,000,001-SNP stress fails under ASan/UBSan; repaired implementation passes |
| Temporary/output ownership | Collision sentinel preserved; normal/fatal cleanup passes with open read handles; an earlier stream-write error is detected even if closing succeeds |
| Native presentation | PowerShell 5.1 direct invocation and Tee-Object exit 0; native generated separators checked; all 37 executables contain the shared process manifest |

The separate cases/preparation commands in the counts are not 129 independent
scientific models. No Mac result or all-input bitwise guarantee follows from
these observations. Pristine failing cases and before-fix sanitizer traces remain
available; corrected boundary/output behavior is not mislabeled pristine parity.

## Findings and repairs

All F IDs below are new; F001 in the root ledger remains the separate fxtract
installation-order finding.

| ID | Classification / severity | Reproducer and cause | Repair / compatibility consequence |
| --- | --- | --- | --- |
| F002 | Upstream, high: heap overflow | `hires`, `cached-hires`, `three-hires`; stale `t` used to scale/copy a covariance print buffer. Pristine ASan reports an out-of-bounds read in `vst`. | Compute the covariance triangle before printing it. Restores the stated mean/variance units; broken upstream output cannot be the expected reference. |
| F003 | Upstream, high: heap overwrite | `diagonly`; `killoffdiag` received the square of the matrix dimension. Linux and Windows abort; ASan identifies invalid writes. | Pass `nl*nr`, the matrix dimension. Other covariance modes retain their calculations. |
| F004 | Upstream, high: incorrect coefficient | `single-source`, `single-auto`; rank-zero A is NULL, so the generic NULL branch returns zero before the one-source rule. Cached/allsnps summaries print coefficient 0. | Handle the one-source rule first in `calcadm` and `calcadmfix`. Coefficient is 1, variance 0. This deliberately corrects scientific output for this broken boundary case. |
| F005 | Upstream, high: invalid dimensions/read | `ratio-single` reads coefficient 2 with one source; ASan catches it. Target-only/right-too-small models also lack the required fit dimensions. | Validate source/right counts and the ratio requirement before fitting/helper launch. Bound fixed-pattern indexing to representable int indices. Valid multi-source fits are unchanged. |
| F006 | Upstream, high: parameter stack overflow | `too-many-pars`, `include-overflow`; capacity checked after writing beyond 400 entries, including recursive includes. | Pass remaining capacity through includes and check before each write. `max-pars` verifies 400 entries remain accepted. |
| F007 | Upstream, high: empty scalar/null reads | `empty-value`, `empty-int`, `empty-dbl`; field 0 read when there are no fields. Windows could silently accept an empty double. | Reject empty scalar parameters with a precise fatal diagnostic. |
| F008 | Upstream/parser safety and Windows encoding | NUL/UTF-16 input, oversized lines, recursive includes, includes leaking handles, duplicate keys split across includes. | Length-aware line reading, NUL/line limits, recursion-depth accounting, included-file closure, flattened duplicate checks and qpAdm parameter-handle closure. Windows strips only an initial UTF-8 BOM; UTF-16/NUL input is rejected with a UTF-8 instruction. |
| F009 | Windows regression, medium: quoted paths | `win-hash-path`; comment stripping cuts a legal quoted path at `#`, before string unquoting. | Respect quotes while stripping Windows parameter comments; reject empty/unclosed quotes. Unquoted upstream semantics remain. |
| F010 | Windows compatibility, high: Unicode/long paths | `win-unicode`, `win-unicode-helper`, `win-long-log`; narrow APIs otherwise use the legacy process code page/MAX_PATH behavior. | Embed a shared UTF-8/long-path-aware, asInvoker manifest in every executable. Japanese input, Chinese parameter argv, a Unicode installation/helper path, `&`, spaces and `#` pass. Long-path policy is machine controlled; no registry setting is changed. |
| F011 | Upstream overflow amplified by Windows port | `auto-long-temp`; `fsx[266]` and unused Windows shell-command formatting overflow despite enlarged neighboring arrays. Pristine ASan/fortify reproduces it. | Own dynamic path strings; Windows never formats the unused shell commands. POSIX command storage is sized from its operands. Normal terminal text is retained. |
| F012 | Windows temporary ownership/cleanup, high | Name collisions could overwrite temporary files; fatal readers leave open CRT handles that deny deletion. `gzip-bad-data` exposed the latter. | Exclusively reserve qpAdm helper temporaries, preserve colliding files, track ownership, clean on ordinary exit/fatalx, and use delete sharing only for reads of owned temporaries. Ordinary user files retain their open policy. Probe leaves both a stream and descriptor open at fatalx and verifies deletion. |
| F013 | Upstream, medium: keeptmp/early-return leaks | `auto-keep` still deleted the fstats file; `single-auto` returned before deleting it. Child failure bypassed helper-file cleanup. | Honor keeptmp for all five files and remove them on normal single-source/error exits when not requested. Explicit helper logs and saved fstats remain user outputs. |
| F014 | Upstream, high: helper failure handling | `auto-fail`; a nonzero POSIX system status was not made negative, followed by `fclose(NULL)` when no fstats existed. | Detect nonzero child status, inspect output only after child success and close only a valid stream. Windows continues native sibling execution without a shell. |
| F015 | Upstream, high: fstats header parsing | `fstats-noeff`, `fstats-tight-eff`; NULL substring arithmetic crashes on an old header, and fixed `+12` skips digits when spacing is tight. | Locate the marker, advance by its actual length and parse whitespace normally. Missing marker uses the existing old-style warning/default; nonpositive/nonfinite values fail. |
| F016 | Upstream, high: fstats population overflow | `fstats-many-pops`; more than 100 population names overwrite the caller's 100-pointer allocation. | Check the existing 100-entry contract before appending; document caller capacity. All current native callers allocate that capacity. |
| F017 | Upstream, high: undefined hash arithmetic | UBSan reports signed overflow/left shifts in the shared hash. Keys beyond 128 bytes also shift by 32 or more. | Define 32-bit wrapping operations while preserving upstream's arithmetic right shifts and observed x86 hash values, including nonzero multiples of 32. All 1,533 probe hashes (lengths 1–511, three hash modes, high bytes) match pristine Linux byte-for-byte. No replacement hash algorithm. |
| F018 | Upstream, medium: long-summary formatting | `four-source-long`; the requested width is immediately overwritten by 5. | Set the default width before applying longsummary, matching the later newmode summary. Only this requested line wrapping changes. |
| F019 | Upstream, medium: invalid sampler counts | `cached-one/zero/negative-boot`, `zero-trials`, `bayes-zero`; invalid allocations/statistics or misleading fallbacks. | Require at least two bootstrap draws when bootstrap/ratio mode uses them, and reject zero trials in newmode. Preserve unused parameters and negative automatic-trial sentinel behavior. |
| F020 | Upstream, high: large block buffer overflow | `qpadm_probe blocks`: 1,000,001 single-SNP blocks exceed a hard-coded million-element vector. Pristine ASan/UBSan fails. | Allocate from SNP count plus the reserved block slot. Repaired sanitizer run prints 1,000,002 slots; sums/order/weights are unchanged. This is a bounds repair, not an optimization pass. |
| F021 | Upstream, high: compressed PLINK dispatch | `plink-ped-gzip`, `plink-bed-gzip`; decompressed filename loses the suffix required for dispatch, and POSIX branches pass the compressed filename to the reader. Both systems reject valid data. | Preserve the recognized suffix and pass the decompressed path. Ordinary and gzipped PED/BED are checked with their companion files and with qpfstats. |
| F022 | Windows, low: CLI error presentation | `cli-invalid`, `cli-missing-argument`; MinGW's short-option diagnostics differ from glibc. | A platform helper keeps glibc wording for qpAdm; options/defaults/exit behavior remain upstream. |
| F023 | Upstream, high: successful exit after lost output | Linux `/dev/full` reproduces exit 0 for qpAdm `mvname`, saved-fstats copying, and qpfstats output. Buffered writer errors and cp status were ignored. | Check stream error and final flush/close for covariance, helper parameters and both fstats precisions; check POSIX copy status. A native probe exercises an earlier stream error followed by successful close. Successful file bytes are unchanged. |
| F024 | Platform diagnostic, low; retained limitation | A short packed read calls perror with errno 0: Linux says `Success`, the Windows CRT says `No error`, followed by the same fatal length/count diagnostic. | Raw stderr difference is recorded; the input fails on both systems and produces no scientific result. Do not normalize arbitrary error lines. |
| F025 | Inherited interface quirks; retained contract | `-v` continues without parameters; help repeats `-V` for details; maxrank/output are legacy behaviors described above. | Preserve upstream behavior and document it. No new options or result-file semantics are inferred. |

Additional small safety repairs: bounded formatting of fatalx diagnostics, and
using the loaded effective-block count for `dofjack` rather than a stale or
uninitialized local. The latter field is not printed or used in these fits.

## Reproduction

Build the port normally. Use **new** output directories for every run:

```powershell
.\build-windows.ps1 -Msys2Root C:\msys64
python tests/windows/audit_qpadm.py --bin bin --output validation-results/T01-windows
python tests/windows/audit_qpadm.py --verify validation-results/T01-windows
```

Run the same Python file under WSL with `--bin` pointing at the pristine pinned
Linux build; run it again against an isolated repaired Linux build. The
`--select` regex permits focused reproductions, e.g. `hires`, `bayes`, `plink`,
`fstats-`, or `empty-`. Then inspect exact diffs:

```powershell
python tests/windows/audit_qpadm.py --compare validation-results/T01-linux validation-results/T01-windows
```

`--compare` retains all differences, including intentional bug fixes and native
termination codes. Its JSON/diff must be reviewed; `--verify` asserts the repaired
success/failure, within-format science, sampler reachability and cleanup contract.
Do not interpret a comparison command completing as a clean parity certificate.

For sanitizer builds use an isolated checkout, build libnick with
`CFLAGS='-g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie'`, and
build qpAdm/qpfstats/convertf/transpose with those flags and
`LDFLAGS='-fsanitize=address,undefined -no-pie'`. Set
`ASAN_OPTIONS=detect_leaks=0:abort_on_error=1` as the runner does. Never instrument
or overwrite the user's installed reference.

`qpadm_probe.c hash` links against each build's real libnick. Its binary output
must match exactly (SHA-256
`b1e22f8e84a007f01778b6ab267ff8ef81c25e1bccddd095b7117cb1140f28d7`).
The Windows `temp`/`fatal` modes test ownership/collisions and open-handle cleanup.
For `blocks`, compile the real `qpsubs.c` with function/data sections, define
`PROBE_BLOCKS` for the probe and link with `--gc-sections` and libnick/scientific
libraries; this isolates the actual block function from unrelated tool globals.

## Closure limits and carry-forward

- Exact parity applies to the recorded inputs/toolchain/thread settings, not
  every possible model, compiler or BLAS version. Fixed broken cases are compared
  with the repaired Linux build and explicitly differ from pristine upstream.
- No macOS machine/build was available. Platform guards and a Linux build were
  checked; macOS runtime parity is not claimed.
- Positive-coefficient rejection sampling can be very slow for poor models;
  its upstream sampling rule and absence of a trial cap are preserved. Tests use
  a bounded process timeout and an informative fixture, not a new statistical rule.
- Forced process termination, power loss, real full-volume/low-memory fault injection,
  network shares and every Windows policy/configuration were not certified.
  Fatalx/ordinary exits and detected gzip corruption/parser failures are covered.
  Linux `/dev/full`, native stream write errors and a failed Windows destination
  copy are checked; those are not a full filesystem-fault certification.
- Process-lifetime leaks are not a leak-free certification. The full real-world
  14 GB analysis previously compared is historical evidence, not rerun here.
  Current large-offset proof uses a sparse 4 GiB file plus focused block stress.
- qpWave/qpfit/qpmix/qpGraph contain analogous private helper-launch code. The
  shared changes are regressed in their existing fixtures where available; their
  own path/ownership/error audits remain T03/T20/T19/T08. They do not inherit a
  T01 pass. Full standalone qpfstats analysis remains T02.
- Inherited help quirks are preserved: `-v` continues without a parameter file,
  and help repeats `-V` where it describes details. No new result file behavior
  is attached to legacy `output` or `maxrank` parameters.

Windows process-manifest references:
[UTF-8 process code page](https://learn.microsoft.com/en-us/windows/apps/design/globalizing/use-utf8-code-page),
[long-path requirements](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation).

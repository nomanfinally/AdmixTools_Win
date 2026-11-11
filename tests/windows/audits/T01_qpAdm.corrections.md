# T01 qpAdm: remaining-issue corrections

Scope notice (11 November 2026): this is historical audit evidence.
Inherited-bug repairs described here are not the current porting baseline.
See [the project-wide restoration](PORT_ONLY_SCOPE_RESTORATION.md) for
active sources, retained Windows adaptations and new reference results.

This follow-up addresses the known issues retained by the initial T01 review,
plus the separate F001 installation-order defect, at the user's request.
The [initial report](T01_qpAdm.md) and its evidence remain historical records;
this report supersedes their retained F024/F025 behavior and sampler limitation.
Current source/build hashes and raw verification are recorded in
[the correction evidence](T01_qpAdm.corrections.evidence.json).

| Finding | Correction and compatibility consequence |
| --- | --- |
| F001: installed fxtract | Copy `perlsrc` helpers before `src/fxtract`, matching upstream `make install`. The installed file must match `src/fxtract` byte-for-byte. This closes the overwrite-order defect, not the independent Perl/shell workflow audit. |
| F024: misleading truncated-input diagnostic | Nonnegative short packed reads now report `read failure (length mismatch): unexpected end of file`, followed by the existing counts and fatal diagnostic. Calling `perror` here previously reported `Success` on Linux or `No error` on Windows, possibly using stale errno. Actual negative read errors still use `perror`. The shared repair gives identical EOF wording; it changes no valid input/output. The expected-byte count also uses the correct printf argument type. |
| F025: misleading CLI and inactive parameters | `-v` prints the version and exits successfully without opening a parameter file or choosing a seed. Help now identifies `-d` correctly and shows the required `-p <file>` invocation. `output:`, `outputname:` and `maxrank:` now fail explicitly with guidance, rather than creating an empty file or silently ignoring the requested rank. Save stdout with redirection or PowerShell `Tee-Object`; qpAdm still performs its established codimension-one and full-rank fits. |
| F043: unbounded sampler and overflowing sample size | Positive-coefficient sampling fails after `maxreject` consecutive rejected proposals for a single sample; the default is 1,000,000. A positive integer can raise/lower the limit. It resets after each accepted draw and does not apply when `positive_coeffs: NO`. Failure produces a nonzero exit and an explicit diagnostic; it does not return a partial Bayesian estimate. Guard `mctrials * nl` before its int-indexed allocation. Widen the rejection diagnostic counter to 64 bits and remove the unused overflowing trial counter. |

The sampler's probability distribution, proposal generation, RNG consumption,
importance weights, matrix calculations and successful result formatting are
unchanged. The finite failure bound is an intentional change from upstream's
unbounded termination behavior. A model that reaches it may have completed after
further attempts in the old implementation. Increase `maxreject` only after
examining model fit; it is not an optimization or a new statistical estimator.
Earlier ordinary-fit output may already have been printed when Bayesian sampling
fails, so always check the exit status before treating a run as complete.

## Verification

Raw artifacts are retained under `validation-results/hard-check/T01-corrections/`.
The correction evidence records actual counts, hashes, commands, exits and exact
comparison results. It distinguishes full matrices from any final focused reruns.
Windows and isolated repaired Linux builds use the T02 correction sources already
present in the worktree, including the shared qpfstats helper lifecycle.
The pristine pinned reference and the user's installed Linux tools are preserved.

| Check | Recorded result |
| --- | --- |
| Full behavior matrices | Windows 137, repaired Linux 133, ASan/UBSan 133; all behavior assertions pass |
| Shared full-matrix cases | 129 cases; all 84 jointly successful cases match both streams exactly after documented metadata substitutions |
| Shared streams including failures | 254/258 exact; only BOM acceptance and malformed-quote handling differ. The old zero-errno wording difference is gone. |
| Final focused matrices | 37 cases per platform/build; all assertions pass and all 74 Linux/Windows streams match. Linux/ASan streams also match. |
| Sampler boundary probes | Six Windows and six sanitizer probes pass, including the default million-rejection limit and per-sample reset |
| Final cross-suite regression | 35 cases across 26 tools; all 70 streams and 18 generated files match repaired Linux exactly; binary round trip exact |
| Pristine cross-suite comparison | 69/70 streams and all 18 files match. The sole stream difference is the already recorded T02 F037 qpGraph population diagnostic correction. |
| Earlier T01 scientific output | Whole scientific tails for default, hires, diagonly, single-source and three Bayesian cases are unchanged; explicit/default rejection limits give the same informative positive fit |
| Build/install/PowerShell | All 37 native executables rebuilt; installed fxtract bytes match upstream-selected source; PowerShell version command prints only `version: 2206.w` and exits 0 |

The full matrices precede only a final correction to the printf argument type
for the expected-byte count in the packed EOF diagnostic. Final focused matrices
and the suite regression use the final rebuilt executables. Raw traces, case
origins and both build metadata snapshots are retained rather than claiming the
earlier full matrices ran against a later binary.

The public `audit_qpadm.py` runner checks corrected help/version, unsupported
parameters without output creation, invalid limits, EOF diagnostics, all existing
scientific modes and an informative positive-coefficient fit with an explicit
limit. Successful fits are compared exactly, without floating-point tolerances.

`qpadm_probe.c`, compiled with `-DPROBE_SAMPLER`, includes the real qpAdm sampler
and substitutes only the Gaussian proposal generator for deterministic boundary
testing. Compile with `-ffunction-sections -fdata-sections`, source/nick include
directories, `--gc-sections`, qpAdm's dependency objects (excluding `qpAdm.o`),
libnick and the normal GSL/BLAS libraries. Windows additionally uses the forced
compatibility header/object and zlib. The evidence records complete commands.
Modes `reject`, `default-limit`, `boundary`, `reset`, `disabled`, and `overflow` check
failure at 3 and 1,000,000 rejected proposals, acceptance after two rejections,
resetting the limit after an accepted sample, an unconstrained draw, and
rejection before an overflowing allocation. These
probes are tests, not installed tools or replacement scientific algorithms.

## Remaining scope

No retained F024/F025 issue or unbounded rejection loop is intentionally left
open after these corrections. `Passed with limitations` remains appropriate:
macOS runtime, all possible inputs/toolchains, exhaustive allocation failures,
forced termination and filesystem/power-loss conditions have not been certified.
Other tools, shared modules and interpreter workflows retain their own audit
items. These coverage gaps cannot be closed by changing a status label.

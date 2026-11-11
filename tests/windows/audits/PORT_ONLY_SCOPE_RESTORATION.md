# Project-wide port-only scope restoration

On **11 November 2026**, the user requested removal of beyond-scope corrections:
retain Windows porting and presentation, and match the unmodified Linux version.
This restoration applies to production code and installed binaries, not just
documentation. Earlier repair reports and their raw evidence remain historical.

The upstream reference is `67bc219174a109951a9434e0a383ec464fb140ee`.
Production restoration starts from the pre-audit Windows port
`a8e87433a8e63008d0163314e84802538219d5c4`, then retains Windows adaptations and
help-only presentation changes. Git history was not rewritten; no commit or push
was made. Pre-restoration source, installed binaries/DLLs, documentation and the
uncommitted diff are backed up under
`validation-results/port-only-restoration/before/`. Raw comparisons and build logs
are retained beside that backup. No user dataset or WSL installation was changed.

## Removed from active production code

- Scientific repairs to sampling/seed application, X ploidy/counting, single-source
  coefficients, rank/covariance cases, tree/jackknife/Fourier calculations and
  other inherited estimator defects. Shared scientific bodies return to the
  pre-audit port; they are not replaced with new algorithms.
- The Bayesian `maxreject` control and finite rejection cap, and changes to its
  counters/allocation guards. Upstream's sampling/termination behavior is restored.
- New scalar/vector parsing rules, duplicate-ID checks, cached-fstats and genotype
  validation, stricter dimensions/block/input domains and shared memory/ownership
  fixes that also changed pristine Linux behavior.
- Version-only exit changes, rejection of inherited inactive parameters/switches,
  extra result/output semantics and upstream output-write error corrections.
  Accepted Linux parameters, ignored controls, defaults and exit paths are restored.
- qpfit's newly enabled fitting path: it again retains upstream's early exit.
- POSIX helper-process, gzip and temporary-file rewrites. Those implementations
  revert to the pre-audit port rather than importing Windows adaptations into Unix.

Known inherited defects remain documented and deferred. For example, the old
single-source all-SNP coefficient behavior is reproduced instead of corrected.
Matching an inherited bug is compatibility evidence, not a scientific endorsement.

## Retained porting and presentation

- Native separate `.exe` programs, `.w` version suffixes, upstream layout, DLL
  closure, the existing Linux-compatible RNG, binary I/O, LP64-equivalent types,
  large offsets, mapping and stack support.
- UTF-8/long-path Windows manifest, native temporary path separators, Windows
  quoted paths and `#`, initial UTF-8 BOM/CRLF parameters and Unicode filenames.
- Native sibling qpfstats/Graphviz execution and file copying instead of POSIX
  shell commands on Windows. Dynamic helper paths, exclusive owned temporaries,
  read-handle delete sharing and native cleanup remain isolated to Windows.
  The retained shared native helper lives in `src/win32/compat.c`; its callers are
  guarded by `_WIN32`. Unix helper implementations remain unchanged from the
  pre-audit port. No shared statistical helper is rewritten for this purpose.
- Windows getopt/gzip diagnostics that match Linux presentation, and corrected
  installation order for `fxtract` so its bytes match upstream's selected source.
- Help describes that version switches continue; qpAdm help correctly labels
  `-d` and `-p <file>`. These are help-text changes only. `-v` is not made to exit,
  inactive options are not rejected, and scientific result formatting is unchanged.

## Validation and source controls

Current hashes, matrices, exact comparisons and case origins are in
[PORT_ONLY_SCOPE_RESTORATION.evidence.json](PORT_ONLY_SCOPE_RESTORATION.evidence.json).
All 37 supported Windows binaries are rebuilt from restored sources; their DLL
and source hashes are checked against `bin/windows-build.json`.

Fresh isolated WSL trees contain the pinned pristine source and the restored
current port. For the 26-tool regression, source bytes in the pristine tree are
verified against Git. Its upstream link ordering needs `LDLIBS=-lnick` on this
toolchain; this is a command-line build control, not a source/statistical repair.
qpfit is a separate build-only exception: its conflicting `void addscaldiag`
declaration is changed to `int` while compiling that executable, then its original
source bytes are restored. The existing early exit remains; no fitting behavior
is enabled. This exception is recorded rather than called an entirely pristine
qpfit build.

Windows uses UCRT64 GCC 16.2.0, GSL 2.8, OpenBLAS 0.3.34 and zlib 1.4. Linux uses
GCC 15.2.0, GSL 2.8 and OpenBLAS 0.3.32. Both use the existing O2/O3 settings,
`-ffp-contract=off -fno-fast-math`, one BLAS/OpenMP thread, `NEHALEM` core selection,
`LC_ALL=C`, fixed fixture seeds and synthetic data. No optimizations were added.

The 35-case suite compares all 70 streams and 18 generated files exactly with
pristine Linux; binary round trips are exact. Focused scope checks exercise
ordinary/limited/seeded/mixed-X analyses, legacy inactive controls, partial numeric
tokens, duplicate IDs, version/help/error options, automatic helpers and gzip.
Windows adds Unicode/quoted paths, long temporary paths, BOM and CRLF cases.
Additional informative Bayesian and single-source runs, and cached qpfit's early
exit, have their own raw manifests. The initial full matrix's qpfit case lacks
cached input and checks its inherited failure; the separate cached-input run
supersedes it as proof of the early exit. They are not conflated.

| Check | Recorded result |
| --- | --- |
| Full focused matrices | 72 Windows, 67 pristine Linux and 67 current-port Linux cases complete; expected success/failure behavior agrees |
| Shared focused streams | 128/134 exact; the six differences are the approved help-text changes, with native abort codes recorded separately |
| Bayesian/single-source supplement | Four cases per build; all eight streams match pristine Linux exactly; the informative sampler is reached |
| Cached qpfit supplement | Exit 0 after upstream's `all OK!`; both streams match the declaration-only reference build |
| Main analysis bodies/shared code | Eight tool `main` functions match the pre-audit port exactly; 12 restored source/header files are byte-identical to it |
| Suite regression | 35 cases, 70 streams and 18 generated files exact against pristine Linux; exact binary round trips |
| Gzip/conversion | Ten shared cases, all compared streams and 12 generated files match; native invalid-gzip/space-path checks complete |
| Python helpers | Twelve generated files match byte-for-byte; ordering, hashes and cleanup assertions complete |
| Windows integration | Unicode/quoted/long paths, BOM/CRLF and owned-temp checks pass; direct PowerShell 5.1 automatic qpAdm with Tee-Object exits 0 |

Comparison uses only recorded metadata substitutions: paths/executable suffixes,
the requested `.w`, CRLF/LF, temporary PIDs, addresses, CPU/memory values and the
auto-seed printed by `-v` without parameters. Scientific numbers/result lines are
not removed and no floating-point tolerance is applied. Help wording improvements
and native abort-code representation are retained as explicit differences, not
hidden by normalization.

The earlier corrected-source `--verify` runners/probes can assert removed repairs
or require removed APIs. Their historical results are not current release checks.
Use `port_only_scope.py`, `parity.py`, `compatibility.py` and `script_helpers.py`
for the restoration evidence and retain the older material for deferred work.

## Remaining limits

This establishes the recorded port-only baseline, not complete hard-audit closure
for every tool/module, input or numerical corner case. Historical passing labels
are superseded; T01-T06 coverage reviews remain pending for this baseline.
Inherited crashes, undefined behavior, nonfinite estimates and ineffective controls
are deferred, not repaired or silently classified as Windows failures. macOS,
every Windows policy/UNC configuration, exhaustive allocation/filesystem faults,
forced termination and power loss are not certified. Long-path cases use this
machine's existing enabled policy. The blocked upstream qpfmvmix target remains
blocked. MSI packaging and optimizations remain later milestones.

Restoring the exact upstream source also restores existing trailing whitespace.
`git diff --check` reports those inherited lines; the evidence check verifies no
new unmatched trailing-whitespace additions. No broad formatting rewrite is
introduced merely to alter this historical source style.

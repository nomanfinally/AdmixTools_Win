# T03 qpWave corrections

Status: **passed with limitations**, 10 November 2026. F045-F054 are fixed.
F055, a malformed-header token-boundary defect found during these corrections,
is also fixed. No requested T03 finding remains open. This closes the tested
qpWave scope; shared modules and other tools retain their independent audits.

The [initial review](T03_qpWave.md) and its evidence remain historical.
[Correction evidence](T03_qpWave.corrections.evidence.json) records the final
sources, executables, build commands, cases, comparisons and artifact hashes.
Raw artifacts are under `validation-results/hard-check/T03-corrections/`.
Changes are uncommitted on `audit-t03-qpwave`, based on `9d764a2`.
Pristine Linux reference remains `67bc219174a109951a9434e0a383ec464fb140ee`;
it was not patched. Corrected Linux and sanitizer builds use isolated trees.

## Repairs and compatibility consequences

| Finding | Repair | Evidence / consequence |
| --- | --- | --- |
| F045 | Parse `seed`, initialize the existing RNG, and apply existing population sampling before building the analysis index. Seed zero preserves the implicit sequence, equivalent to 1. | Limit 3 selects 24 analysis rows from eight six-person populations. Seeds 77/123 match independently constructed physical subsets at every printed rank/matrix value. Repeats and 0/1 agree; high-bit seed also agrees across OSes. Unlimited/direct-default output is unchanged. Limited analyses intentionally differ from pristine's broken 48-row behavior. No RNG or sampling algorithm was replaced. |
| F046 | Parse complete representable block labels; reject labels outside the SNP-sized table before indexing. Check count/padding/copy bounds before allocation in the shared block helpers. Negative labels retain upstream's ignore behavior. | IDs 2221 and INT_MAX on 2,200 SNPs fail before writes; partial numeric labels fail too. qpAdm rejects the same malformed inputs. A valid dense assignment through label 2199 completes. Windows/Linux/sanitizer checks find no table overrun. Valid labels, block order, weights and printed block-count convention are retained. |
| F047 | Validate population minimum/order, wide products, int matrix lengths and addressable covariance bytes before allocation. | The real guard accepts the last supported asymmetric dimension (2,46341) and rejects its next value, square overflow, negative/INT_MAX and one-population dimensions without large allocations. The 218-by-218 file case fails safely. |
| F048 | Require finite positive block size and finite diagonal settings; reject zero-dimensional models before OAS. Validate the chromosome count before incrementing it. | Zero/negative/NaN block sizes, nonfinite diagonals and one-left/right inputs fail explicitly; ordinary OAS/diagonal/eigen/rank modes retain their numerical results. No statistical default changed. |
| F049 | Share one validated reader behind `loadfstats` and `loadfstatsx`. Require complete finite numeric tokens, a matching basis header, the required nonbase means and covariance records, and consistent duplicate values. Track presence separately from numeric zero. | Missing/invalid/partial/infinite mean values, conflicting records, and missing covariance now fail before fitting. Valid zero values remain valid. Full files and graph population subsets pass; reversing valid records preserves rank output. qpAdm, qpfit, qpGraph, qpfmv and qpmix reject malformed required records. Existing division/scaling, symmetric assignments and calculation order for valid files are unchanged. The serialized contract is a complete basis for the consumer's populations; omitted cells no longer imply zero. |
| F050 | Call the existing individual-ID validator before loading genotype data. | Duplicate IDs fail for text, ancestry, packed and transposed inputs. Existing unique-ID formats and gzip modes pass. |
| F051 | Reject inactive `output/outputname/oldallsnpsmode/numboot/details` controls explicitly, close the parameter handle, make `-v` exit after its version line, and correct the usage synopsis. | Existing output sentinels remain byte-identical after rejection; no file is truncated. Version-only output has one line and empty stderr. Parent/consumer tests omit qpAdm/qpfit-only controls when invoking qpWave. Use shell redirection, not an inactive result-file parameter. No legacy estimator or bootstrap mode was invented. These are intentional interface repairs relative to upstream's misleading/no-op behavior. |
| F052 | Assign rank metadata from `effblocks`, independently of the local scratch variable used by eigenanalysis. | Direct/cached/automatic and eigenanalysis cases retain identical rank output; the uninitialized `y` assignment is gone. The currently unused field now has the intended value. |
| F053 | Map native zlib header/EOF/CRC/length errors to the corresponding GNU gzip diagnostics. Print the Linux parent `perror` wording for a format failure with no parent errno. | Raw normalized stderr matches corrected Linux for corrupt, truncated, empty, one-byte, CRC and length failures. No stderr lines are removed from comparison. Input files are preserved and incomplete decompressed files are removed. Other storage/permission/codec-diagnostic combinations are outside this six-case claim and remain part of M01/M11. |
| F054 | Reject failed mappings before returning an object; close the descriptor on failure and unmap if object allocation fails. Validate file/dimension products and the int fields actually stored in `genFile`; open the input read-only. | Native Windows and Linux forced-failure probes terminate through the intended fatal path; no failed object returns. A real Linux address-space-limited 4-GiB mapping also fails safely. Read-only transposed input succeeds, including qpAdm integration. Valid mapping output format is unchanged. |
| F055 | Bound the shared base-population lookup by the number of populated tokens, including the required following value. | A header ending at `basepop:` now fails with the expected missing-base diagnostic on Windows/Linux/sanitizers. Previously the lookup read an uninitialized token slot; pristine's recorded run consumed an unrelated population name. This is an upstream parser defect, not an intentional format feature. |

The initial F044 Windows option-diagnostic repair is retained. Version stays
`2201` / Windows `2201.w`. The suite layout, executable names, result precision,
rank ordering, floating-point operations and scientific defaults are retained.
Ordinary valid calculations are not changed to match malformed or broken inputs.

## Final verification

| Check | Result |
| --- | --- |
| qpWave matrix | 145 Windows, 145 corrected Linux and 145 ASan/UBSan cases pass behavior assertions. Pristine runs the same 145 cases and retains its original defects; it is not expected to pass the repair assertions. |
| Exact platform comparison | All 73 jointly successful cases have exact scientific rank/matrix output and generated-file bytes. 72 also have identical complete normalized streams. The remaining `forward-paths` case echoes deliberately different Windows/Linux input quotation; that difference is retained. No scientific tolerance is used. |
| Scientific before/after | Among previously successful cases that still succeed, only the six direct limited-sampling/seed variants change scientific output. Each belongs to F045 and is validated against a physical subset. |
| Sanitizers | Corrected cases and affected-caller failures show no ASan/UBSan report. Mapping and dimension probes reject before invalid operations. Leak detection remains disabled; this is not a leak-free certification. |
| Shared consumers/helpers | The existing consumer/helper/boundary matrix passes: 60 Windows cases, with the 16 common consumer/preparation cases also passing on Linux and sanitizers. Valid common streams/data compare exactly. |
| Shared failure paths | 23 additional cases each on Windows, Linux and sanitizers: malformed required means/numbers/covariance in five cached consumers; malformed blocks in qpAdm/qpWave; valid largest dense block label; qpAdm transposed input. All pass. T01's specific F046/F049/F054 recheck requirements are satisfied within this scope. |
| Existing integration suite | 35 cases and generated scientific files match Windows/Linux exactly under its documented metadata substitutions; both binary genotype round trips are exact. This exercises other users of the changed shared modules. |
| Windows native behavior | PowerShell 5.1 redirection/Tee, installation paths with spaces/Unicode, sibling helper lookup, long forward-slash temporary paths, native printed backslashes, gzip cleanup, and read-only input pass. |
| Large offsets | Fresh size/seek/binary-map probes beyond 4 GiB pass on Windows and Linux. This is a service-level check, not an end-to-end large scientific dataset. |
| Guard/failure probes | Last/first-invalid asymmetric and square matrix boundaries plus minimum/order/negative/INT_MAX cases pass without huge allocations. Real Linux and injected Windows/Linux mapping failures reach the intended fatal path. |

Windows rebuilt all 37 native targets using UCRT64 GCC 16.2.0, GSL 2.8,
OpenBLAS 0.3.34 and zlib 1.4. Corrected Linux uses GCC 15.2.0, GSL 2.8 and
OpenBLAS 0.3.32. `-std=gnu11 -ffp-contract=off -fno-fast-math`, upstream
`-O2`/libnick `-O3`, 32-bit BLAS integers and the Windows 8-MiB stack remain.
The default Linux tools and regression targets were also rebuilt with explicit
flags; the final Linux matrix was rerun against that resulting executable.
Sanitizers use an isolated non-PIE build with frame pointers and debug symbols.
All comparisons use single-thread dependency settings, `LC_ALL=C`, fixed seeds,
and the existing controlled `NEHALEM` OpenBLAS setting; no CPU-specific code was
introduced into the port.

The comparison normalizations remain those listed in the initial report:
paths, PID/temp names, command operand quotation, CRLF, `.exe`/`.w`, addresses,
CPU time and memory. Scientific/result lines and file bytes are retained.
Raw abnormal exit codes still differ by OS (POSIX signals versus Windows abort
codes); the programs retain fatal/abort behavior. Windows BOM/quoted-space-path
support is an extension. Those differences are recorded, not silently mapped to
exact exit/status parity.

A final trailing-space cleanup in `qpsubs.c` has identical preprocessed code;
the evidence retains both the tested source hash and the cleaned source hash.

A preliminary Windows run timed out after already printing a fatal diagnostic;
it was not counted as passing. The final captured-output runner suppresses
inherited interactive OS error dialogs while retaining the real child exit code.
The final matrix completes and passes. Earlier fixture/build explorations stay
in the raw directory; final evidence identifies the authoritative runs.

Remaining limits: no macOS execution, Windows ASan/MSan, full research-dataset
or end-to-end >4-GiB analysis, alternate compiler/BLAS certification, full
resource-leak audit, storage-exhaustion/permission fault matrix, or forced
termination/power-loss cleanup audit. Independent M/H items and full audits of
the other consumers remain pending. These limits do not leave a requested
F045-F054 repair open and do not constitute full-suite parity certification.

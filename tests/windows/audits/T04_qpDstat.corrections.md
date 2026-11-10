# T04 qpDstat defect corrections

Status: **all 23 recorded findings corrected in their reproduced scopes**, plus
new parser finding F073 corrected, 10 November 2026. The independent module and
header audits remain incomplete; this is not a full-suite compatibility pass.

These repairs were requested after the audit-only delivery. The
[original findings](T04_qpDstat.md#findings), source snapshots and raw evidence
are retained. [Correction evidence](T04_qpDstat.corrections.evidence.json)
records current source/executable hashes, build commands, exact comparisons,
case outcomes, independent oracles and remaining raw differences.

## Repairs and regression scope

| Finding | Corrected contract and source | Recorded regression |
| --- | --- | --- |
| F024 | `mcio.c`: distinguish a negative read from transposed EOF; never diagnose EOF using stale errno. | `truncated-tgeno`; identical diagnostic on Windows/Linux. |
| F044 | `qpDstat.c`: use the existing guarded Windows getopt adapter. | Both invalid option and missing operand, stdout/stderr retained. |
| F045 | `qpDstat.c`: parse/initialize the existing RNG and apply population limits before building analysis indices. | Seeds 77/123 match independently sampled physical subsets; zero/one/high-bit seeds and repeatability retained. |
| F048 | `qpDstat.c`: require a finite positive block size, finite jackquart and a chromosome count whose X index is representable. | Zero/negative/NaN/Inf and INT_MAX rejection; valid/custom blocks unchanged. |
| F050 | `qpDstat.c`: validate duplicate individual IDs before mapping/loading genotypes. | Duplicate IDs rejected; ordinary text/packed/transposed/ancestry/PED/BED and id2pops paths pass. |
| F051 | `qpDstat.c`: version-only exit; reject unsupported output and inactive controls before opening any output file. | Existing output sentinels preserved; version-only text; each inactive control rejected. |
| F056 | `qpDstat.c`: index the six local tree distances by local pair position, retaining global indices only for input lookup. | Four/five-population runs; an independent additive tree with pendants 1,2,3,4 and internal branch 5 gives the expected lengths under all 24 relabelings in a five-population index. |
| F057 | `qpDstat.c`: check banker types/indices, replace the fixed population-presence buffer with four-element membership checks. | Bad type rejected; bounded 101-population legal-selection probe succeeds; no type-1 population rejected explicitly. |
| F058 | `qpDstat.c`, `egsubs.c/.h`: bounded typed/untyped loaders and a checked quartet population append. | Population/typed-list capacity probes reject before writing outside arrays. The legacy typed API retains its documented caller-capacity precondition; the production caller uses the bounded API. |
| F059 | `qpsubs.c`: lag-k correlation uses the available `g+1-k` elements, stopping before a one-value correlation; check dimensions and spectrum, remove signed index-product overflow, free both weight workspaces. | Fourier sizes 0/1 reject; 2/5/12/32 succeed; full/Five-block modes pass ASan/UBSan. Constant vectors and nonpositive spectra fail explicitly. |
| F060 | `qpDstat.c`: return the computed SD directly instead of reconstructing it from estimate/Z. | Balanced estimate zero prints oracle SD **0.218218**; ordinary D/f4, weighted/missing and permutation oracles pass at printed precision. |
| F061 | `geno.c/.h`: exact integer padding, checked dimensions/products/allocation and bounded 48-byte headers; allow normal minimum-row padding. | Valid five-sample normal matrix round trips; SIZE_MAX allocation and oversized header reject safely. |
| F062 | `geno.c`: validate fstat, complete header, all fields, dimensions and exact file length before mapping a live matrix. | Empty/short/malformed/negative/zero/overflow/junk/hash/length probes reject; failed objects stay empty and destructible. |
| F063 | `geno.c`: close descriptors on every failure, reset failed objects, check full-read allocation. | Sixteen repeated failures leave zero extra handles/descriptors on both platforms. |
| F064 | `geno.c`: check output open/allocation/write/close; open binary files in binary mode. | Missing-parent writer and transpose reject; Linux `/dev/full` verifies buffered write/close error handling; ordinary binary round trips remain byte-exact. |
| F065 | `xsearch.c`: express wrapping hash multiplication and left shift using unsigned operations. | Extreme-key hash outputs match across Windows/Linux/ASan and match the retained pre-repair native output; UBSan is clean. |
| F066 | `regsubs.c`: print the n-element RHS as a vector and free all singular-return workspaces. | Singular and nonsingular direct regressions, tree modes; ASan/UBSan clean. |
| F067 | `egsubs.c`: close typed-list input on successful completion; bounded typed loader also checks numeric type/offset range. | Sixteen repeated loads leave zero extra handles/descriptors. |
| F068 | `getpars.c`: remove complete LF/CRLF endings before macro storage/substitution. | LF, CRLF, included parameter files and actual qpDstat macro paths pass on both platforms. |
| F069 | `sortit.c`: free the median workspace before the one/two-value early returns. | Correct medians and LeakSanitizer-enabled probe pass. |
| F070 | `qpDpart.c`: retain the caller's ownership of the borrowed colprobs row. | Multiple-quartet sibling run succeeds on Windows/Linux and under ASan; T22 itself remains pending. |
| F071 | `mcio.c`, `strsubs.c/.h`: create Unix gzip temporaries exclusively, register ownership for fatal cleanup, recurse through common reader returns, then release; invoke gunzip with argv. | All supported gzip formats and corrupt/truncated/reader-fatal paths leave no newly owned temporary; Windows native cleanup remains effective. No pre-existing file is removed. |
| F072 | `qpDstat.c`: reject tree corrections with fewer than two observed alleles in a used population/SNP. | Haploid X tree fixture rejects before tree output, without NaNs or a regression memory error. No new haploid estimator is introduced. |
| F073 / medium | `getpars.c`, scalar/vector integer and real readers: replace silent partial atoi/atof conversions with checked conversions; retain decimal/boolean syntax and caller responsibility for finite scientific domains. | New inherited input-integrity finding: `M03-parser-invalid` exits zero and converts `7oops` to 7 on both pre-repair platforms; its retained initial-run streams reproduce this. Malformed/out-of-range scalar, vector, real and 64-bit integer tokens now reject; valid boundary/vector parsing agrees on both platforms. |

F073 was reproduced during the repair checks and assigned the next stable ID.
It affects parameter-parser callers throughout the suite. NaN/Inf remain
syntactically valid real tokens in the shared parser; qpDstat validates their
scientific domains locally. No shared nonfinite-value policy was invented.

## Validation

- Three fresh isolated builds: UCRT64 Windows, corrected Linux and corrected
  Linux with ASan/UBSan. The original pinned pristine Linux build at
  `67bc219174a109951a9434e0a383ec464fb140ee` was retained for comparison.
  The installed `bin/` and previous reference builds were not overwritten.
- **147 qpDstat cases per build**, **91 Windows / 89 Linux module cases**,
  and **59 shared qpWave cases on Windows and Linux** pass their behavior
  verifiers. Module counts differ because three services are Windows-only and
  `/dev/full` is Linux-only. Expected fatal-input rejections retain real statuses.
- All **75 jointly successful qpDstat cases producing scientific rows** agree
  between Windows, corrected Linux and sanitizers at printed precision. The
  independent allele-count/jackknife, sampling and 24-relabeling tree oracles pass.
  There are no unexpected scientific-row differences from the retained native
  baseline or pristine Linux among jointly successful cases.
- **92/147 full Windows/Linux terminal comparisons** are exact under the narrow
  metadata normalization. Other differences are OS abort statuses, absolute
  user-input paths, and established Windows BOM/quoted-path extensions. The two
  corrected-Linux/sanitizer stream differences are absolute fixture paths.
  Raw correlation/tree output and all comparison diffs remain available.
- Module comparisons are **89/89 exact** between corrected Linux and sanitizers;
  **61** are exact across Windows/Linux, with raw platform statuses and
  platform-only cases retained. The native process argument oracle passes.
- Raw 3,200,000-byte RNG output is identical across the three builds, SHA-256
  `b62c398efd682e2a935d20d3239103c1ea5c0b72711d4719dffc0083777bb0cc`.
  Packed/binary genotype round trips are byte-exact. The six selected raw module
  outputs, including hashes and tree relabelings, also match exactly.
- No sanitizer finding appears in the authoritative matrices. The median probe
  enables LeakSanitizer. Other sanitizer runs disable whole-process leak checks
  because upstream tools retain unrelated process-lifetime allocations.
- Native PowerShell 5.1 direct invocation, separate streams, Tee-Object, spaces,
  forward-slash temporary paths and gzip pass with equal result text and no owned
  file remaining. Source snapshots agree with the actual repaired worktree.

Compilers/dependencies and FP/thread controls are unchanged from the original
audit: Windows GCC 16.2, GSL 2.8, OpenBLAS 0.3.34, zlib 1.4; Linux GCC 15.2,
GSL 2.8, OpenBLAS 0.3.32. BLAS integers remain 32-bit, dependency threads one,
LC_ALL=C, OpenBLAS core NEHALEM, no fast-math/reassociation and FP contraction off.

Authoritative native artifacts are under
`validation-results/hard-check/T04/repairs/verified-*`; Linux raw data/probes are
archived as `repairs/linux-repairs-evidence.tar.gz`. Use GNU tar with sparse-file
support when extracting its mapping-failure fixtures. Earlier `initial`,
`final-*` and initial build directories are exploratory evidence, superseded by
the `verified-*` runs, and are not a repair pass.

The repair archive is 84,551,066 bytes, SHA-256
`5135548e7dd46d1f9a2134ad82b96c0157f32c9a6d89c03318cb32f33bca2b73`.

## Intentional upstream differences and remaining limits

Sampling now honors its parameter and seed. Tree pair indexing and zero-estimate
SD are corrected on both platforms. Those scientific differences from buggy
pristine output are identified by finding and case; ordinary calculations retain
upstream order/defaults and are compared without widened numerical tolerances.
Unsupported output/control parameters now fail explicitly; use shell redirection.
Single-allele tree corrections, degenerate Fourier inputs and malformed numeric
tokens are rejected instead of producing undefined or misleading results.

The 18 independent module reports still contain unexecuted functions/contracts.
Their M/H entries remain pending, T22 has only its targeted ownership regression,
and T04 remains unpassed for completion of those audit limits. macOS runtime,
Windows sanitizers, every allocation/storage failure, large research datasets and
an end-to-end >4-GiB scientific analysis remain unverified. No commit, push,
release, installer change or suite-wide certification was made.

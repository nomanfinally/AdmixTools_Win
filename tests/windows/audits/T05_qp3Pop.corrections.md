# T05 qp3Pop corrections

Scope notice (11 November 2026): this is historical audit evidence.
Inherited-bug repairs described here are not the current porting baseline.
See [the project-wide restoration](PORT_ONLY_SCOPE_RESTORATION.md) for
active sources, retained Windows adaptations and new reference results.

Status: **all 14 recorded finding groups corrected in their reproduced scopes**,
11 November 2026. T05 has passed with limitations. The original
[audit](T05_qp3Pop.md), [evidence](T05_qp3Pop.evidence.json), module inventory
and raw failing runs remain historical. Independent M/H audits and T04's broader
coverage closure remain pending; this is not full-suite parity certification.

[Correction evidence](T05_qp3Pop.corrections.evidence.json) records actual source,
executable, manifest and stream hashes, comparisons, behavior checks, independent
oracles, native checks, installed build provenance and retained raw differences.

## Repairs

| Finding | Corrected behavior | Evidence |
| --- | --- | --- |
| F044 | qp3Pop uses the shared Windows getopt adapter behind `_WIN32`. POSIX keeps getopt. | Invalid option and missing operand preserve Linux diagnostic wording and stream routing, with raw OS fatal statuses retained. |
| F045 | The existing RNG is seeded before any possible use. Population limiting still occurs before analysis indices are constructed. | Seeds 77/123 match their separately sampled physical subsets; CLI seed, repeats, zero/one/implicit defaults and high-bit seed also pass. No PRNG or permutation algorithm changed. |
| F048 | qp3Pop rejects nonfinite/nonpositive block sizes, unrepresentable X chromosome index and invalid trimming fractions. Shared `estjackq` checks its own entry domain and actual rounded trim count before using trimmed pointers/counts. | NaN/Inf, zero/negative blocks, INT_MAX numchrom, `.5`/excessive trimming and four-block rounded trimming reject without sanitizer errors. Valid ordinary/trimmed results retain their calculation order. |
| F050 | Existing duplicate-individual validation runs before genotype loading/mapping. | Duplicate IDs reject; normal text/packed/transposed/ancestry/PED/BED readers and conversions pass. |
| F051 | `-v` prints its one version line and exits. Inactive `-b` and parsed legacy/output controls reject explicitly; parameter handles close. Explicit `-V` remains enabled throughout the requested run. | Version/help/CLI cases pass; existing output sentinels survive rejected output requests. The help now describes the effective `-s` option. Ordinary quiet output is unchanged. |
| F074 | The low-data path uses the same workspace and owned-stream cleanup as normal completion. Main owns its multi-triple stream; direct calls own and close their own stream. | Sixteen low-data calls leave **zero** extra handles/descriptors. LeakSanitizer is enabled for the dedicated probe and reports no leak. A one-SNP details case retains its buffered rows. The upstream no-data row remains unchanged. |
| F075 | `loadaa` accumulates inbred pair counts in `double`, as its existing count products already do, instead of converting each update through 32-bit int. Its verbose count format changes consistently to `%6.0f`. | Balanced 150,000-person diploid probe now gives `top=-0.000005000100`, `bot=0.500010000200`. The large mixed-ploidy X probe gives `top=-0.000005555679`, `bot=0.500011111358`. Both match independent pair counts; explicit float-cast UBSan is clean. Ordinary small integer counts and calculation ordering are preserved. |
| F076 | Type bounds precede the indexed inbreeding-array read. | Negative and first-out-of-range type probes pass ASan and match physically omitting that row exactly. Ordinary valid local type assignments are unchanged. |
| F077 | A negative triple-parser status is rejected before it can become an allocation count. The population-list multiplication also has an int-bound guard. | Malformed triples produce the explicit malformed-input diagnostic, without a negative calloc request or sanitizer failure. Valid colon/extra-column/line-selection behavior is retained. |
| F078 | Main opens one details stream for the analysis and writes triples in popfilename order. Existing SNP fields, spacing, precision and line format remain unchanged; no new headers are added. | Two triples retain **4,400** detail rows, rather than the last 2,200. Single-triple CLI/parameter details and cross-platform bytes after CRLF conversion pass. |
| F079 | README.3PopTest and Windows guidance explain that outgroupmode does not bypass the target-heterozygosity protection, the required inbreed/override distinction and the arbitrary `.001` scale. | No-hets/outgroup alone still rejects; inbreed/outgroup and explicit applicable override paths pass. The scientific protection was not removed to accommodate the old documentation. |
| F080 | A nonpositive/nonfinite accumulated f3 denominator is rejected before jackknife or result output. Ordinary per-block epsilon arithmetic is unchanged. | Fixed-target normalized analyses reject for both ordinary override and inbreed paths. The explicit outgroup alternative remains finite. No automatic mode switch or partial huge f3 is printed. |
| F081 | Details output checks error state, flush and final close; failures use the existing fatal stderr style. | Native Windows/Linux closed-pipe injection rejects. Linux `/dev/full` rejects before any result row, including ASan. Successful details output is unchanged in format. No disk was filled. |
| F082 | Both ordinary and PED individual readers initialize `hasxhets` from declared sex: **F diploid; M/U retain the existing haploid convention**. The shared allele reader and estimator are unchanged. | Independent female-only, mixed-sex, mixed weighted, all-male and unknown-sex X oracles pass. Mixed X now prints `-12.463104 3.198725 -3.896 100`. The same oracle passes after packed, transposed, ancestry, PED and BED conversion. |

F082 defines the missing metadata initialization using the existing sex column
and existing `hasxhets` branches. It introduces no new estimator or ploidy
inference. Unknown sex is not silently promoted to female. `inbreed` controls
the within-individual correlation correction; it does not infer sex. Female
pseudodiploid homozygous records can still use the documented inbreed correction.
Default autosomal filtering/sex conventions and male/unknown X behavior remain.

## Validation and intentional upstream differences

- **167 qp3Pop cases each** on fresh isolated Windows, corrected Linux and
  corrected Linux with ASan/UBSan pass their behavior verifiers. Probe builds
  record their own source hashes. The sanitizer probe additionally recompiles
  qpsubs with explicit floating-to-integer overflow checking.
- All **75 jointly successful result-producing cases** match Windows/Linux/ASan
  at upstream's printed precision. Eight further jointly successful no-data
  cases also match. All independent allele/pair-count and jackknife oracles pass.
  No numeric tolerance was added and no scientific result line was removed.
- Compared with the original Windows and pristine Linux runs, the only changed
  jointly successful scientific rows are the four seed-dependent cases (F045)
  and four X-enabled/mixed-ploidy cases (F082). Previously invalid settings,
  duplicate IDs, inactive controls and zero-denominator analyses now reject.
  Details retention and verbose/CLI diagnostics deliberately repair broken
  upstream behavior. Full row-by-row before/after values remain in the evidence.
- Full qp3Pop terminal/status/file comparisons: **107/167** exact Windows/Linux
  and **165/167** exact Linux/ASan after the previously enumerated metadata
  substitutions. The other raw differences are retained: OS fatal statuses,
  absolute user-input paths and established Windows BOM/quoted-path extensions.
  The two Linux/ASan differences are absolute path operands. Exact result and
  generated-data comparisons are enforced separately from OS abort statuses.
- Fresh shared-module matrices: **91 Windows / 89 Linux / 89 ASan** cases pass,
  including native and Linux mapping failures, large offsets, process services,
  RNG, matrix round trips, parsers, sampling, ownership and sibling consumers.
  Full module comparisons are **61** exact Windows/Linux and **89/89** exact
  Linux/ASan; remaining differences are platform-only cases and raw exit codes.
- Affected-consumer behavior checks pass on all three builds: **145 qpDstat**,
  **22 selected qpAdm**, **32 selected qpfstats**, and **57 selected qpWave**
  cases per build. All 73 jointly successful qpDstat result-producing cases
  match across platforms. qpAdm comparisons are 22/22 exact; qpfstats are 31/32
  exact across Windows/Linux with one raw abort-status difference, and 32/32
  Linux/ASan. qpWave is 57/57 exact Linux/ASan; its Windows differences are
  expected rejection statuses. These remain scoped regressions, not new full
  audits of those executables.
- Native PowerShell 5.1 direct invocation, separate streams, Tee-Object, spaces,
  forward-slash temp input and gzip cleanup pass. The ordinary and installed
  executable both retain `710.w`; the corrected Linux executable retains `710`.

The original pinned Linux reference was neither patched nor overwritten.
Requesting a broader pristine build encountered qpfit's already documented
`addscaldiag` declaration conflict; that log remains. Corrected Linux/ASan
builds succeed, and comparisons use the retained pristine T05 reference with
zero source mismatches against upstream `67bc219174a109951a9434e0a383ec464fb140ee`.

Build settings and dependencies are recorded in evidence and logs. Windows is
UCRT64 GCC 16.2.0, LLP64; Linux is GCC 15.2.0, LP64. The upstream Makefiles append
their optimization flags (`-O2` for ordinary objects, `-O3` in the nick archive)
to the supplied CFLAGS; full commands are retained rather than inferring flags
from CFLAGS alone. Floating-point contraction/fast-math remain disabled, BLAS
integer ABI is unchanged, thread counts are one and locale is C. No timing,
address, path or OS-status substitution removes scientific differences.

## Installed artifacts and retained evidence

All **37 supported native executables** rebuilt successfully using the normal
Windows build entry point so shared readers/estimators are current throughout
`bin/`. This is a build result, not full-suite parity certification. The previous
bin bytes and their hashes are preserved under
`validation-results/hard-check/T05/repairs/installed-before/` and
`installed-before.json`.

The installed qp3Pop passes native PowerShell checks and direct comparisons for
seeded sampling, mixed/female X and multi-triple details. Installed build/source
and executable hashes are recorded. No commit, push, release or MSI was created.

Authoritative Windows artifacts are under
`validation-results/hard-check/T05/repairs/`, particularly `verified-windows`,
`modules-windows`, the affected-consumer directories, `native-powershell`,
`installed-powershell` and `installed-checks`. Linux originals are under
`/home/user/t05-repairs-build/`. The separate sparse
`repairs/linux-artifacts.tar.gz` retains corrected sources/builds, results,
probes and supplemental evidence; extract on a sparse-capable filesystem.

`verify_t05_repairs.py` validates completed matrices, original comparisons,
source/build hashes, independent oracles, supplements and installed provenance.
Its machine evidence reports no verification failures. Original harness bytes
are retained under `repairs/original-harness/` and match every original audit
harness hash. Earlier repair diagnostics remain separate from `verified-*`.

Remaining limits: no macOS runtime, complete scientific run exceeding 4 GiB,
all real research datasets, exhaustive allocator/race/encoding fault matrix,
or independent contract completion for every linked function/header. These
limitations remain explicit in the queue; no recorded T05 defect is left open.

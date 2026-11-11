# T04 qpDstat hard review

Scope notice (11 November 2026): this is historical audit evidence.
Inherited-bug repairs described here are not the current porting baseline.
See [the project-wide restoration](PORT_ONLY_SCOPE_RESTORATION.md) for
active sources, retained Windows adaptations and new reference results.

Follow-up: all recorded defects were subsequently corrected at the user's
request; see [corrections and current evidence](T04_qpDstat.corrections.md).
Independent module/header coverage remains incomplete. The original audit
below and its machine evidence are preserved as the pre-repair record.

Original audit status: **reviewed with open defects; not passed**, 10 November 2026.
No production source, scientific default, calculation order, RNG, CLI behavior
or terminal formatting was changed. This is an audit and regression-evidence
delivery, not a defect-repair release or a parity certification.

The port baseline is `f0e642a` (the committed T03 corrections), on
`audit-t03-qpwave`. The pristine reference is
`67bc219174a109951a9434e0a383ec464fb140ee`. T03's historical reports and scoped
passes are preserved. Some local mistakes repaired in qpWave also exist in
qpDstat; their finding IDs are reused with an explicit T04 scope below.

[Machine evidence](T04_qpDstat.evidence.json) records source/executable hashes,
commands, dependencies/ABI, cases, raw exit statuses, stream hashes, oracles,
comparisons and the Linux archive hash. Raw artifacts live under
`validation-results/hard-check/T04/`; final Linux inputs, streams, sanitizer
reports, gcov and probe-build commands are in `linux-evidence.tar.gz`.
The GNU sparse archive preserves the logical 4-GiB mapping-failure inputs.
Earlier incomplete/incorrect-fixture explorations are retained separately and
are not authoritative evidence.

## Modes, connected code and independent modules

| Path | Contract exercised |
| --- | --- |
| Explicit quadruples | D/f4, 24 permutations, colon syntax, repeated populations, extra/missing columns, line ranges and CLI/parameter precedence |
| Population-list enumeration | Four/five populations, three pairings per quadruple, ordering, best marker, banker types and forceclade control |
| Statistical variants | Sample-size weighting, printed SD/count controls, custom/automatic blocks, block gaps/ignored sites, Fourier, few-block warning/override and tree estimation |
| Genotype selection | Population limits and seeds against physical-subset oracles, ID-to-pop mapping, missing data, bad SNPs, chromosome inclusion/exclusion, custom chromosome count and genetic/physical maps |
| X chromosome | Mixed-sex data, xmode on/off, whole-data xdata and explicit chromosome 23; xmode's haploid counter is selected only with an explicit X chromosome |
| Formats and platform | EIGENSTRAT, packed ancestry, transpose, ancestry records, PED/BED, concatenated gzip members, corrupt/truncated files, read-only mapping, paths, BOM/CRLF/UTF-16/NUL and native PowerShell |
| Shared helper consumers | qpAdm, qpfstats, qpWave, qp3Pop, qp4diff, qpF4ratio, qpdslow, qpDpart and transpose; qpWave direct/cached/automatic helper regressions |

qpDstat's own upstream diff is only the platform include and `1160.w` suffix.
Its normal link inputs include M11–M14 and M17–M20 plus libnick and native M01.
Archive membership is not a call graph. In particular, qpDstat itself does not
launch qpfstats or perform cached rank fitting; those paths were checked as
independent M01/M17 consumer regressions.

All 18 requested modules received their own report, compiler-derived function
and header inventory, review warnings and relevant direct/integration probes:

| Modules | Reports |
| --- | --- |
| Native services and strings | [M01 compat](M01_compat.md), [M02 strsubs](M02_strsubs.md), [M03 getpars](M03_getpars.md) |
| RNG and sorting | [M04 gauss](M04_gauss.md), [M05 gds](M05_gds.md), [M06 sortit](M06_sortit.md), [M07 xsearch](M07_xsearch.md) |
| Mathematics | [M08 vsubs](M08_vsubs.md), [M09 statsubs](M09_statsubs.md), [M10 linsubs](M10_linsubs.md) |
| Data and mapping | [M11 mcio](M11_mcio.md), [M12 geno](M12_geno.md), [M13 mapfile](M13_mapfile.md), [M14 admutils](M14_admutils.md) |
| Analysis helpers | [M17 qpsubs](M17_qpsubs.md), [M18 egsubs](M18_egsubs.md), [M19 ldsubs](M19_ldsubs.md), [M20 regsubs](M20_regsubs.md) |

[The function inventory](T04_modules.inventory.json) contains 1,096 native
compiler-recognized function definitions across 30,520 source lines, their
declarations/locations, call/reference candidates, header closure, platform
directives and Linux execution counts. **Independent module coverage is still
incomplete.** Each report lists unexecuted functions and remaining contracts;
no M/H item is passed by this review. This distinction is essential: adding an
inventory or exercising a function does not complete its hard audit.

## Validation and interpretation

- Four isolated builds: native UCRT64 Windows, pristine Linux, current Linux
  port, and non-PIE Linux ASan/UBSan. Production sources match the frozen
  snapshot; pristine sources match the pinned Git object byte-for-byte.
- Full qpDstat matrices contain **146 cases per build**, including preparation.
  An additional haploid/tree interaction is retained as a focused eight-case
  run (seven repeated preparation cases, one new analysis).
- Independent module/caller matrices contain **72 Windows / 69 Linux cases**
  per build; three Windows-only cases test native platform services. Eight
  focused parser cases add four new include/length/capacity scenarios, and one
  transpose output-error case is retained separately.
- The shared qpWave regression has **59 cases on Windows and Linux**, including
  cached/direct/automatic modes, malformed blocks/individuals, gzip diagnostics
  and helper lifecycle. Its behavior verification passes; it is not a new full
  audit of qpWave or the other consumers.
- Independent allele-count and weighted block-jackknife oracles match ordinary
  D/f4 estimates, errors, counts and all 24 permutations at printed precision.
  The deliberately balanced zero-statistic oracle exposes F060.
- All **87 jointly successful qpDstat cases emitting scientific rows** in the full Windows/
  current-Linux matrices match at printed precision. Across all 146 cases,
  **106 full terminal comparisons** are exact after the documented metadata
  substitutions. This includes failures with matching streams; it does not
  erase differing raw statuses or unsafe paths that happen to exit zero.
  Help/version and zero-exit cases with no result rows are listed separately;
  they do not count as scientific comparisons. The insufficient-block case,
  for example, terminates with a message and exit zero instead of a result.
- Packed and binary transpose round trips are byte-exact. The raw RNG check
  compares 3,200,000 bytes across eight seeds, including high-bit seeds, without
  text normalization. File hashes and actual exceptions are retained.
- Native PowerShell **5.1.26100.9818** direct execution, separate redirection,
  Tee-Object, a parameter filename with spaces and gzip with a forward-slash
  STMP pointing to a space-containing directory succeed. Result text agrees;
  generated Windows temp paths use backslashes and no owned file remains.

Windows uses GCC 16.2.0, GSL 2.8, OpenBLAS 0.3.34 and zlib 1.4; Linux uses
GCC 15.2.0, GSL 2.8 and OpenBLAS 0.3.32. Exact flags/configuration strings are
in the evidence: GNU C11, upstream O2/O3, no fast-math, contraction off,
32-bit BLAS integers, single dependency threads, LC_ALL=C and controlled
OpenBLAS core selection. No alternate compiler/BLAS combination is certified.

Comparisons retain every scientific/result line and raw abnormal exit code.
The normalizer changes only CRLF, known executable suffixes, `.w`, mapping
addresses, CPU/memory values and the exact generated gzip temp operand/required
command-operand quotes. Binary RNG bytes and scientific files are never
normalized. Absolute user-input path echoes and Windows BOM/quoted-path
extensions remain visible differences. POSIX SIGABRT/SIGSEGV and Windows abort
codes are not made equal. Comparison commands intentionally return nonzero
for these differences and the unresolved defects.

## Findings

All findings below were **open at the original audit snapshot**. Their subsequent
repairs are recorded separately above. An inherited defect is not evidence of
Windows correctness.

| ID / severity | Reproducer, observation and affected code | Classification and proposed repair |
| --- | --- | --- |
| F024 / medium, additional reader occurrence | `truncated-tgeno`: `mcio.c:3091` calls perror after a nonnegative short read. Linux prints `Success`, Windows `No error`. Both reject the file. | Inherited EOF misuse with a Windows terminal mismatch. The earlier packed-reader F024 repair remains valid; extend its length-vs-negative-read handling to this transposed reader. |
| F044 / medium, T04 occurrence | `cli-invalid-option`, `cli-missing-value`: MinGW wording/quotation differs from glibc. | Windows regression. qpDstat has not selected the existing `admix_getopt` adapter used by corrected qpWave; reuse it behind a platform guard and compare both streams. |
| F045 / high, T04 occurrence | `popsizelimit` equals default; seeds 77/123 agree with each other but disagree with their independently sampled 15-person physical subsets. Source builds analysis indices before setplimit and never parses/initializes its seed. | Inherited silent selection defect. Apply the existing sampler before constructing indices, parse/initialize the existing RNG, and compare corrected Linux and Windows subset oracles. qpWave's F045 repair stays closed. |
| F048 / medium/high, T04 occurrence | Zero/negative/NaN/infinite block sizes are accepted; INT_MAX chromosome count triggers signed-overflow UBSan at `numchrom+1`. | Inherited local validation gap. Validate complete finite settings and representable chromosome counts before arithmetic; retain valid defaults. This does not reopen the corrected qpWave code. |
| F050 / medium, T04 occurrence | `duplicate-ind` exits zero; direct `M11-duplicate` proves the existing validator rejects the same IDs. | Inherited missing caller validation. Validate IDs before genotype loading in qpDstat and recheck every input format and id2pops mapping. |
| F051 / medium, T04 occurrence | `output`/`outputname` replace an existing sentinel with an empty file; results remain on stdout. `-v` prints a version plus a no-parameters message/tool header. colcalc/fullmode/nostatslim/msjack controls and forceclade have no operative analysis path here. | Inherited misleading interface. Reject unsupported controls or separately specify their implementation; do not invent legacy statistical behavior. Preserve ordinary stdout and document redirection. |
| F056 / high | `tree-five`: gettreelen allocates six-element arrays but uses global pair index `h` to address them (`qpDstat.c:1349–1350`). ASan reports heap overflow. Pristine Linux crashes; Windows can print additional corrupted results and exit zero. | Inherited memory/scientific defect. Index six local pairs by `i`, retain the global index only for reading f2, and verify four/five-population permutations and missingness on corrected Linux. |
| F057 / high | `banker-type3` writes past cc[3]; `banker-many` writes 101 entries into zz[100] in islegal. ASan identifies both stack overflows; ordinary builds can accept them. | Inherited bounds defects. Validate banker types and size the population-presence vector from checked dimensions; retain legal quartet ordering. |
| F058 / high | `poplist-capacity` and `quad-capacity` name more populations than the 54-person-sized buffers. ASan reports writes beyond eglist/ztypes. `M18-capacity` reproduces typed-list caller overflow independently. | Inherited capacity contract. Count/check names before writes and use bounded typed/untyped loaders; keep the upstream file syntax and ordering. M18 and all list callers require checks. |
| F059 / high | `fourier`, `fourier-five` and direct M17 Fourier probes: lag correlation length `g-k+2` reads past g+1 arrays. g=0 also writes beyond zero-length work arrays. ASan reports the actual shared qpsubs.c path; ordinary results/termination are unreliable. | Inherited shared numerical/memory defect. Establish the intended lag/window contract, bound all arrays and require valid dimensions before computing; retain every correlation/result line in corrected-reference comparisons. Do not infer a scientific repair from a tolerance. |
| F060 / medium scientific output | `oracle-zero`: estimate 0, independent SD **0.218218**, printed SD **1.000000** on all ordinary builds. qpDstat initializes serr to 1 when Z=0 instead of retaining the computed SD. | Inherited printed scientific error. Return the actual jackknife SD from getdsc and preserve the established output precision/order. Check both explicit and generated quartets, including zero variance. |
| F061 / medium/high | `M12-small-normal`: valid five-sample normal allocation aborts because padding is tested against 4 rather than the minimum 48-byte row. SIZE_MAX allocation is unchecked; `M12-header-size` writes 66 bytes into the 48-byte header buffer. | Inherited dimension/header/allocation defects in geno.c. Use checked integer byte calculations, validate addressable/serializable dimensions, check allocation, and make header writing bounded. No format redesign. |
| F062 / high | `M12-read-invalid`: a 48-byte `TGENO invalid` header can be accepted in the sanitizer run or produce uninitialized dimension-dependent sizes elsewhere. sscanf's result is unchecked; short-header and fstat validity are not established before use. | Inherited malformed-header integrity defect. Require a complete bounded header, parsed field count, valid dimensions/products and file length before constructing a live matrix; verify no scientific content is silently synthesized. |
| F063 / medium | `M12-map-leak`: 16 empty-file read attempts leave **16 descriptors/handles** on Windows and Linux. genotype_matrix_read_file returns -2 before closing fd. | Inherited resource defect, separate from corrected M13 constructMap. Close fd on every read/map outcome and specify/restore the failed object's state. |
| F064 / medium/high | `M12-write-missing` passes a missing-parent output path; unchecked fopen returns NULL and fwrite faults. The actual transpose executable rejects its own missing-output case through its exit path, recorded separately. | Inherited M12 API failure handling. Check output open/write/close before dereference, preserve errno/diagnostic routing, and recheck writer consumers. Do not generalize the direct API crash to every caller. |
| F065 / medium/high | `M07-hash`: UBSan reaches signed shifts in xlhash; xhash2 also has unchecked signed multiplication for extreme keys. Ordinary tested hashes agree across OSes. | Inherited undefined arithmetic outside already repaired hash paths. Specify existing modulo-bit behavior with unsigned operations and retain ordinary/extreme hash oracles; no new hash algorithm. |
| F066 / high | `M20-singular` and `tree-haploid`: regressit prints rr as an n-by-n matrix although rr has n entries (`regsubs.c:58`). ASan reports the read through printmatwl. | Inherited error-path memory defect. Print the correct vector shape, release all failure-path allocations, and test singular/nonfinite callers without changing successful fitting order. |
| F067 / medium | `M18-file-leak`: 16 loadlist_type calls leave **16 descriptors/handles** on both platforms; egsubs.c omits fclose. | Inherited lifetime defect. Close the file on normal completion and cover malformed/early exits and repeated callers. |
| F068 / medium | `crlf-macro` / `M03-parser-crlf`: macro DIR/ROOT contains a residual carriage return; substitution splits the resulting pathname. Both Linux and Windows reproduce it on identical CRLF bytes. | Inherited CRLF input defect especially relevant to Windows authoring. Strip the complete line ending before substitution while preserving internal whitespace/quoting; test LF/CRLF and includes. Verified workaround: UTF-8 parameter files with LF. |
| F069 / low | `M06-median-leak`: LeakSanitizer records 8- and 16-byte allocations leaked by median's one/two-value early returns. | Inherited library leak. Free the temporary array on both early returns; verify median values and repeated use. |
| F070 / high, T22 follow-up | `caller-qpDpart`: first patternscore frees borrowed `cp`, the last colprobs row (`qpDpart.c:702`); the second quartet reads it at line 657. ASan reports heap-use-after-free; Windows faults. | Inherited sibling-tool ownership defect. Keep row ownership in the parent and free only owned work buffers. Record under T22; this targeted discovery is not a complete qpDpart audit. |
| F071 / medium, Unix lifecycle | Focused gzip ownership run: current Linux leaves decompressed text/packed/transposed and reader-fatal temp files under /var/tmp; pristine also leaves early-return temporaries. Windows cleans its owned inputs. | Inherited Unix lifecycle issue. Share owned cleanup across reader returns/errors while preserving Windows behavior. The runner hashes/removes only files absent before that invocation and leaves pre-existing files alone. |
| F072 / medium/high scientific/error path | `tree-haploid`: one male per population on X, xmode/inbreed enabled. setf2 computes 0/0 at t=1; ordinary builds print NaN tree diagnostics and can exit zero. ASan subsequently reaches F066. | Inherited haploid tree correction gap. Establish the upstream-supported haploid tree contract, use the applicable finite correction or explicitly reject unsupported tree inputs before output; do not guess a new estimator. |

Repaired shared block-label guards F046, mapped-object failure handling F054
and the tested gzip format diagnostics F053 remain effective in the current
port paths. Pristine intentionally differs in these corrected failure cases,
gzip PED/BED detection and parameter-parser repairs. Existing T01–T03 passes
are scoped historical evidence; no module-wide clean pass is inferred.

## Architecture, presentation and closure

The thin native port architecture is appropriate. Keep individual executables,
upstream source layout, scientific loops and shared compatibility helpers.
Use the existing diagnostic adapter, bounded list helpers, checked dimensions
and explicit ownership rather than adding a dispatcher or duplicating Windows
process/file logic inside scientific functions.

Useful Windows improvements are truthful help, early validation, safe errors,
quoted/native generated paths and reproducible documentation. Terminal colors,
banners, reordered results, changed precision, automatic logs, optimizations
and changed scientific defaults would violate this project's contract.
The legacy shell helpers remain visibly separate from the native gzip/helper
paths; their existence must not be presented as full Windows support.

T04 remains **unpassed**. No production repair, commit, push or release was
made. The 18 independent module reports are an evidence-backed review with
explicit remaining function/contract gaps, not completed full-module audits.
macOS, Windows sanitizers/MSan, full research datasets, an end-to-end >4-GiB
scientific analysis, exhaustive allocation/storage/permission failures and
forced termination remain unverified. Close reproduced defects and fill the
listed coverage gaps before marking the respective tool/module/header passed.

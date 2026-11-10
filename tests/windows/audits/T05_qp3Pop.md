# T05 qp3Pop hard compatibility audit

Status: **reviewed with open defects; not passed**, 10 November 2026.
Historical review: the [11 November corrections](T05_qp3Pop.corrections.md)
close all 14 recorded finding groups in their reproduced scopes. The original
source/evidence and findings below are preserved; T05 is now passed with limitations.
This delivery changes audit code and documentation only. Production sources,
installed `bin/`, branches and commit history were left unchanged.

The compatibility baseline is upstream
[`67bc219174a109951a9434e0a383ec464fb140ee`](https://github.com/DReichLab/AdmixTools/blob/67bc219174a109951a9434e0a383ec464fb140ee/src/qp3Pop.c).
Port HEAD is `05780fbcbaa509fbe17be140999b1224bfdfa7ba`, on the existing
`audit-t03-qpwave` branch. The local qp3Pop file differs from that baseline only
by the platform include and `ADMIX_VERSION_SUFFIX`: Windows correctly reports
`710.w`, Linux `710`. Shared dependencies contain earlier port/bug repairs.

[Machine evidence](T05_qp3Pop.evidence.json) retains source/executable/input and
stream hashes, actual statuses, build settings, raw scientific rows, independent
oracle answers, per-case comparisons, supplemental probes and native checks.
[Connected-module review](T05_connected_modules.md) and its
[1,102-function inventory](T05_modules.inventory.json) distinguish exercised
paths from uncompleted independent M/H audits. No related item is certified by
being linked to qp3Pop.

## Result and scientific evidence

- Fresh isolated Windows, pristine Linux, current Linux, current ASan/UBSan and
  coverage builds each ran **137 cases**. The authoritative directories are
  `complete-windows` and `complete-{linux,pristine,asan,coverage}`.
- All **78 jointly successful cases emitting result rows** match Windows/current
  Linux and Windows/sanitizers exactly at printed precision. All **75** such
  cases shared with pristine Linux also match. These counts include defective
  controls and degenerate estimators; numerical agreement does not make them
  correct. Missing scientific output on either side is retained separately.
- Independent allele/pair-count and unequal-block jackknife calculations match
  ordinary, inbred, outgroup, size-weighted, missing-data, all six distinct
  triple permutations and all-male haploid-X fixtures. No floating-point
  tolerance or scientific-line deletion is used.
- The **mixed female/male X oracle fails** on Windows and pristine/current Linux
  (F082). Expected `-12.463104 3.198725 -3.896 100`; actual
  `-38.924419 7.339204 -5.304 78`. The latter is also the all-male result.
- Seeded physical subsets demonstrate that the parsed seed is ineffective
  (F045). A 150,000-person direct probe demonstrates an independent inbreeding
  accumulator failure (F075). Both defects reproduce in pristine Linux.
- **102/137** full Windows/current-Linux terminal/status/file comparisons are
  exact after the substitutions below. Linux/current versus pristine is
  **120/137**; Linux/ASan **131/137**; Linux/coverage **135/137**. Remaining
  raw differences are retained, including Windows CLI wording, OS fatal statuses,
  absolute input paths, sanitizer diagnostics, Windows input extensions and
  earlier intentional shared-parser/gzip repairs.
- Fresh shared checks: **80 Windows / 78 Linux / 78 ASan** cases pass their
  scoped behavior verifiers. There are **54** full exact Windows/Linux module
  comparisons and **78/78** Linux/ASan comparisons. OS-specific cases and raw
  error statuses account for the other comparisons. These are probes, not
  completed independent module audits.

## Contract and mode trace

`main` reads parameters, SNPs/individuals/genotypes, selects populations using
`setgk/gkignore`, filters chromosomes, reads triples, optionally limits population
sizes, constructs SNP blocks, then calls `dopop3/dof3score` for each triple.
`dopop3` selects individuals, assigns three local types, checks target
heterozygosity unless inbreeding/override is enabled, and prints upstream's
column header and result/no-data row. `dof3score` uses
`f3sc -> loadaa -> getrawcolx/f3scz`, accumulates numerator/denominator by block,
optionally applies sample-size weights, and calls `estjackq -> weightjack`.

| Surface | Checked behavior and limits |
| --- | --- |
| CLI | No arguments, `-h`, `-p`, missing parameter file, invalid option, missing operand, `-v`, `-V`, `-f`, `-L/-H`, `-s`; inactive `-b` confirmed by source tracing. F044/F045/F051 remain open for this tool. |
| Normalized f3 | Default target-heterozygosity denominator; source/source/target order, upstream precision and result ordering retained. Ordinary independent oracle passes. Zero denominator is defective (F080). |
| Outgroup/inbreed/override | All combinations needed for ordinary and no-heterozygote targets exercised. Outgroup denominator remains upstream's arbitrary `.001`, not a new normalization. Inbred oracle passes at ordinary size; F075/F079/F082 remain. |
| Weighting/jackknife | `sizeweight`, `jackweight`, `pubjack`, ordinary trimming, `.5`, excessive and nonfinite `jackquart`, one block, sparse/negative/malformed block IDs. Weighted oracle passes; invalid domains remain F048. Trimmed/unweighted statistical semantics were compared across builds, not independently rederived in every combination. |
| Selection | `chrom`, `nochrom`, `noxdata`, `xdata`, `numchrom`, explicit X, bad SNPs, limited/unlimited populations, seeds 77/123/repeats/CLI, seeded physical subsets, line ranges, empty/malformed/colon/extra-column triples. |
| Inputs | EIGENSTRAT text, packed normal/transposed, ancestry records, PED/BED; gzip variants, corrupt/truncated/CRC/reader-fatal gzip, missing/truncated text, invalid genotype, empty records, duplicate IDs, missing/repeated populations. Binary round trips are byte-exact. |
| Output | Both terminal streams and real exit statuses retained; single/multiple/CLI SNP-details paths, missing parent, existing ignored-output sentinels, `/dev/full`, no-data rows. Details bytes match between platforms after CRLF conversion, including the reproduced overwrite. |
| Windows | Native PowerShell 5.1 AMD64 direct invocation, separate redirection, `Tee-Object`, parameter/cwd paths with spaces, quoted Unicode/metacharacter data paths, BOM/CRLF, forward-slash input/temp paths, gzip and owned-temp cleanup. Ordinary result text is identical. UTF-16 input rejects. |
| Helpers | Actual `convertf`/`transpose` data preparation and qp3Pop-output-to-`qpBound` workflow pass across builds. qp4diff/qpF4ratio ordinary and shared block-guard regressions pass. qp3Pop itself launches no scientific helper process or interpreter. Other helper/tool audits remain separate. |

Source tracing also confirms that parsed `gfromp`, `details`, `output`, `f3log`,
`outpop`, `nostatslim`, `baseval`, `dumpname` and `loadname` do not implement the
suggested controls here. Their matrix cases are recorded; `output` and `f3log`
leave existing output sentinels untouched while exiting successfully.
`dof2score`, `sol2`, `bumpm/bumpw` and local `readpopx` are stale/unreached by the
current executable modes. They are not extra supported scientific modes.

## Findings

All entries below are **open for T05**. Reused F IDs identify another occurrence
of an existing finding, not a reversal of the earlier tool's scoped repair.
Raw reproducers are the named case directories; ordinary cases use
`qp3Pop[.exe] -p par` from that directory. Direct probes use
`qp3pop_probe[.exe] <mode>`. Pristine reproduces the inherited behavior unless
the row specifically identifies Windows presentation or a direct-API boundary.

| ID / severity / classification | Reproducer, actual behavior and cause | Smallest proposed direction |
| --- | --- | --- |
| F044 / medium / Windows regression | `cli-invalid-option`, `cli-missing-value`: Windows says `unknown option -- z`; Linux says `invalid option -- 'z'`. qp3Pop still calls raw `getopt` at `src/qp3Pop.c:435`. | Use the existing guarded `admix_getopt` adapter, retaining stderr/stdout and error exit behavior. No new Windows presentation layer. |
| F045 / high / inherited scientific control | `limit-77`, `limit-123`, repeat and CLI seed: limiting changes the sample, but seeds 77/123 yield identical results and disagree with both explicitly seeded physical subsets. `seed` is parsed but there is no `SRAND` call before `setplimit`. | Initialize the existing PRNG before its first use; retain permutation order and effective unlimited/default behavior. Compare corrected Linux and Windows against physical subsets, including default/high-bit seeds. |
| F048 / high / inherited input/UB | Nonpositive/nonfinite block sizes can exit zero with scientific results; NaN/Inf jackquart silently fall through. `quart-large` reaches a negative allocation count in `estjackq/weightjack`; `numchrom-intmax` triggers signed `numchrom+1` overflow under UBSan. | Validate scientific domains and representable X index before data loading; bound trimming against the number of usable blocks. Shared parser syntax checking alone is insufficient. |
| F050 / medium / inherited input integrity | `duplicate-ind` exits zero and emits results on all ordinary builds. qp3Pop omits the existing duplicate-ID validator before reading genotypes. Duplicate SNPs do reject. | Call the existing individual-ID check before genotype load/mapping; regress all formats and selection paths. |
| F051 / medium / inherited interface | `cli-version` prints two version lines plus stderr `no parameters`, despite help promising exit after version. Parsed controls listed above are inactive; output/log requests succeed without creating results. `verbose` is reset after the first SNP. | Adopt earlier tools' truthful version/unsupported-control policy with explicit preserved help/stream tests; do not invent a new scientific output format or restore speculative legacy algorithms. |
| F074 / medium / inherited lifetime | `probe-early-return`: 16 `dof3score` low-data calls leave **16 open handles/descriptors** on Windows/Linux/pristine. LeakSanitizer records **9,216 bytes in 96 allocations** in the optimized sanitizer probe. `totnum <= 1` returns before workspace frees and SNP-details fclose (`qp3Pop.c:836`). | A shared cleanup exit must cover normal and no-data returns; retain upstream's no-data row/exit contract. Test repeated low-data triples with details enabled. |
| F075 / high / inherited scientific/undefined cast | `probe-inbreed-large`: 50,000 individuals per population, balanced homozygotes. `loadaa` stores pair counts such as **2,500,000,000** in `int jhet` (`qpsubs.c:4374`). Actual `top=0.464752659853`, `bot=-0.429505319706`; independent expected `top=-0.000005000100`, `bot=0.500010000200`. Explicit float-cast UBSan reproduces in both pristine and current qpsubs. | Use a representable pair-count accumulator without changing successful ordinary calculation order; update its diagnostic format consistently. Regress haploid/mixed ploidy, large diploid counts, and all `loadaa` consumers. |
| F076 / high / inherited shared-API bounds | `probe-negative-type`: `loadaa` reads `aainbreed[a]` before checking `a < 0 || a >= aanum` (`qpsubs.c:4296`). ASan reports a read four bytes before the allocation. Ordinary qp3Pop assigns valid local types; this is **not** evidence of a reachable default qp3Pop crash. | Move both type bounds before every indexed read; retain the existing skip contract and test negative/upper-bound types in direct callers. |
| F077 / medium / inherited malformed-input handling | `bad-triples`: `getnamesstripcolon` returns `-nbad`; qp3Pop treats it as a row count and calls `ZALLOC(plists, -1, ...)` (`qp3Pop.c:258`). ASan reports calloc size overflow. Ordinary builds fail as an allocation error, after printing the bad line. | Check the parser status before any row-count allocation; preserve valid line filtering and distinguish malformed input from memory exhaustion. |
| F078 / medium / inherited output loss | `details-multi`: two triples produce two terminal results, but only **2,200** detail rows survive instead of 4,400. `dof3score` opens the same path with `w` for each triple (`qp3Pop.c:752`). The surviving file is the last triple's details. | Establish one explicit multi-triple details ownership policy; open/close at the matching lifetime or reject unsupported combinations. Preserve established per-SNP fields/precision; do not add unrequested terminal banners. |
| F079 / low / inherited documentation mismatch | `no-hets-outgroup` still rejects with the inbreed/override diagnostic. README.3PopTest presents outgroupmode as the remedy for targets without heterozygotes; the independent target-het gate runs first (`qp3Pop.c:371`). | Explain the required inbreed/override setting and `.001` scale in Windows usage documentation. Do not bypass a scientific protection merely to make the documented shortcut run. |
| F080 / high / inherited degenerate estimator | `fixed-target` and supplemental `fixed-inbreed-*`: zero target heterozygosity, positive informative SNP count; normalized output exits zero with f3 **11988234690656.615234**, Z **126.346**. The jackknife's epsilon hides a globally zero denominator. Outgroup mode gives the finite intended alternative. | Detect an undefined normalized denominator before jackknife/result output and provide the existing applicable error policy. Do not remove epsilon globally or silently switch modes. Regress zero/positive target heterozygosity and valid outgroup analyses. |
| F081 / medium / inherited write-error handling | Supplemental `full-file-{linux,pristine,asan}` sends SNP details to `/dev/full`: **exit 0, empty stderr**, normal completed scientific output despite losing details. `fprintf/fclose` errors are ignored (`qp3Pop.c:805-875`). Windows disk-full injection was not performed. | Check detail writes and final close, keeping the upstream stderr style; retain successful output bytes. Pair with F074/F078 ownership repairs and test native output failures without filling a disk. |
| F082 / high / inherited X-ploidy contract | `oracle-x-mixed` fails the independent mixed female-diploid/male-haploid count oracle; `oracle-x-male` passes. All ordinary builds report identical mixed/all-male results, discard female heterozygotes, and count 78 rather than 100 usable polymorphic SNPs. Input readers zero-initialize `Indiv.hasxhets`; no production assignment was found, while `getrawcolx` uses that field rather than gender (`qpsubs.c:477`). | Establish upstream-supported diploid/pseudohaploid X semantics before setting this field or explicitly rejecting unsupported mixed inputs. Add female-only/mixed and direct field-boundary oracles. Any correction changes current/pristine X results and requires separate corrected-reference evidence. |

F075/F076/F082 require targeted rechecks in other `loadaa/getrawcolx` consumers,
including earlier audited tools' X/inbreeding paths. Their recorded ordinary
autosomal comparisons are not invalidated; they never certified every shared
function/ploidy boundary. No numerical tolerance was changed for these findings.

## Architecture and Windows presentation

The port's local architecture is appropriately small: the scientific tool stays
in its upstream source, native I/O/PRNG/temporary services are shared, and no
wrapper, dispatcher, custom progress display or parallel estimator is needed.
The main risks are inherited global state, unchecked domains, output ownership
and uninitialized ploidy metadata, rather than missing Windows visual styling.

Use the existing compatibility adapter for CLI wording. Keep the upstream table,
spacing, numeric precision, result ordering and two output streams. Generated
gzip temporary paths in the native PowerShell test use backslashes even when
`STMP` is supplied with forward slashes; owned temporary files are removed.
Do not change user-supplied path spelling when echoing parameters. Improve user
guidance around quoting, redirection, f3 normalization, no-data rows, inbreeding,
SNP details and known limitations. Dead-code/global cleanup can be a later small
upstream-friendly change after defect repairs; this audit does not recommend a
repository redesign, changed PRNG, optimized summation or new statistical mode.

## Build, reproduction and comparison policy

Windows: UCRT64 GCC **16.2.0-6**, `x86_64-w64-mingw32` (LLP64), ordinary sources
`-O2`, nick archive `-O3`, `-std=gnu11 -fno-common -ffp-contract=off
-fno-fast-math -D_FILE_OFFSET_BITS=64 -D__USE_MINGW_ANSI_STDIO=1`, forced shared
compatibility header and 8-MiB stack. Installed build packages: GSL **2.8-1**,
OpenBLAS **0.3.34-1**, zlib **1.4-2**. Only the actually required runtime DLLs
are copied; qp3Pop's isolated suite needs `libwinpthread-1.dll` and `libz-1.dll`.

Linux/WSL: GCC **15.2.0**, `x86_64-linux-gnu` (LP64), GSL **2.8**,
OpenBLAS **0.3.32**, zlib **1.3.1** package. Linux CFLAGS are
`-std=gnu11 -ffp-contract=off -fno-fast-math` (no explicit optimization flag).
ASan adds address/undefined checks, frame pointers, debug info and non-PIE;
supplemental qpsubs probes explicitly add `float-cast-overflow`. OpenBLAS config
has no `USE64BITINT`; qp3Pop's actual Linux dynamic dependencies are libc/libm,
not BLAS/GSL. No BLAS ABI is silently substituted. Every matrix fixes thread
counts to 1, `OPENBLAS_CORETYPE=NEHALEM`, `LC_ALL=C`, `STMP=tmp`; seed 77 is
explicit except dedicated variants. Build/source hashes match the snapshots;
pristine source hashes match the pinned git objects with **zero mismatches**.

Raw Windows artifacts: `validation-results/hard-check/T05/`. Linux originals:
`/home/user/admixtools-t05/`. Its retained `linux-artifacts.tar.gz` is sparse;
extract on a sparse-capable filesystem because module large-file probes contain
logical files beyond 4 GiB. See [runner instructions](../README.md#t05-qp3pop).

Comparison permits CRLF/LF, executable `.exe`, the requested `.w` suffix,
CPU/memory/address metadata, and the generated gzip temporary operand/quoting
already enumerated by `audit_qpdstat.normal`. All original streams remain.
User-input absolute paths, scientific values, warnings and OS statuses are
**not** normalized away. Generated genotype data compare byte-for-byte; detail
text permits only CRLF conversion. Platform-specific BOM/quoted Unicode support
and prior fixed CRLF/numeric-parser/gzip failures are identified, not disguised
as pristine equivalence. The comparator exits nonzero while any raw difference
remains; the verifier exits nonzero for the documented defects.

Initial diagnostic runs are retained but not authoritative. They exposed an
incorrect initial inbred oracle correction, invalid X block labels and stale
probe expectation text; these harness issues were corrected before the complete
matrices. The mixed-X oracle discrepancy remains explicitly open. Probe-builder
scope and the initial unused Windows qpWave map-failure link attempt are recorded.
The final shared-probe build uses the new `--skip-map` switch and succeeds;
the helper's default T04 behavior is unchanged.

## Closure and remaining limits

The scoped T05 review is recorded; **no clean compatibility or scientific pass**
is claimed. Findings need requested repairs and corrected-reference comparisons.
The 18 related M items and transitive H items remain pending. T04's independent
coverage closure also remains pending despite the user's requested progression
to T05. Other native tools retain their own queue IDs.

Not performed: full research datasets, a complete >4-GiB scientific analysis,
native allocator/disk-exhaustion injection, concurrent external file mutation,
all Unicode/long-path encodings, every legacy parameter/format combination,
independent trimmed-jackknife derivations, exhaustive branch/ownership proof for
1,102 shared functions, or a macOS build/runtime. Native large-file service
checks and successful guarded Linux builds are evidence only for their tested
scope. No installer, release, commit or push was created.

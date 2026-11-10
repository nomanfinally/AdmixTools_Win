# T05 connected modules and tools

Status: **scoped review with open findings; independent M/H items pending**,
10 November 2026. See [T05](T05_qp3Pop.md) for the mode contract, defects, build
settings and raw artifact locations. This report does not inherit a module pass
from T01-T04 fixtures or from a successful qp3Pop link.

Historical review: [T05 corrections](T05_qp3Pop.corrections.md) repair the
recorded shared findings and recheck affected consumers on 11 November.
The function inventory/source hashes below describe the original audit snapshot;
independent M/H audits remain pending after these scoped corrections.

## Dependency boundaries

The ordinary native link contains `qp3Pop.c`, `qpsubs.c`, `mcio.c`, `mapfile.c`,
`ldsubs.c`, `admutils.c`, `egsubs.c`, `regsubs.c`, `geno.c`, the nick archive,
and Windows compatibility/resource objects. A direct object link does not imply
that every function in the object executes. The actual f3 path uses string/file
and parameter services, genotype access, population selection, chromosome/block
construction, allele moments, optional RNG/sample weights, sorting and the
weighted delete-block jackknife. It does not perform graph optimization, rank
fitting, Bayesian sampling, gzip through a scientific helper, or a qpfstats
subprocess. Shared gzip decompression still uses each platform's owned service.

[The inventory](T05_modules.inventory.json) comes from a fresh Windows compiler
declaration/warning scan: **18 modules, 1,102 function declarations**. It records
source hashes, declaration lines, transitive headers and reference/call
candidates. Reference candidates are source-search navigation, not a verified
call graph. Warning counts are not accepted findings without a reproducer.

Linux coverage shown below is aggregate qp3Pop-mode/direct-probe reachability
from diagnostic and completed coverage runs; it excludes the separately built
shared-module matrix. A nonzero function count is not a branch, bounds,
ownership or scientific audit. Zero means no execution in that instrumented
set, not proof that a module cannot be reached under other inputs.

| Item | qp3Pop coverage: executed/declarations | Current evidence and contract check | Still unresolved or independently untested |
| --- | ---: | --- | --- |
| M01 Windows compatibility | N/A / 25 | Fresh native binary, file/gzip cleanup, paths, PowerShell streams; separate I/O/process/services/RNG/large-file probes pass. Backslash temp output retained. | qp3Pop bypasses the getopt adapter (F044). All Win32 allocation/error/concurrency/long-path contracts are not certified. Linux coverage cannot certify Windows branches. |
| M02 strsubs | 32 / 121 | String/file operations, colon triple parsing, missing paths, selected legacy-shell services, owned gzip lifecycle; malformed triple status traced to its caller. | F077: caller treats negative parser status as a count. Full parser capacities, all shell users and every line/file ownership path remain pending. |
| M03 getpars | 13 / 23 | Scalar/vector bounds, CRLF macros/includes, malformed/overflowing numeric tokens, BOM/Unicode platform extensions and unsupported encoding diagnostics. | Shared syntax checks do not establish finite scientific domains (F048). Includes, quoting and all encodings are not exhaustive. |
| M04 gauss | 0 / 2 | Separate Gaussian/reseed probes pass; fixed-seed ordinary RNG binary output matches across platforms. | Gaussian paths are not part of qp3Pop's f3 estimator. Distribution tails/statistical quality and all consumers remain independent work. |
| M05 gds | 1 / 40 | Actual `ranperm` population selection, independent physical subsets, seeds 0/1/77/123/high bit in separate sampler probes. | F045: qp3Pop does not seed the generator. Other distribution/sampling/error APIs remain unvalidated here. |
| M06 sortit | 10 / 18 | Triple/population lookups, block-trimming sorting, equal-value/vector/median and empty-input probes; median leak regression remains effective. | Every equal-key/platform order, type variant, null/alias/overflow contract and helper consumer remains pending. |
| M07 xsearch | 9 / 23 | Genotype name lookup/hash paths, selected extreme hashes, duplicate diagnostic regression. | Hash agreement is not an exhaustive collision, capacity or lifetime proof. Existing unsigned arithmetic repairs remain separate from T05's missing ID-validator call. |
| M08 vsubs | 36 / 257 | Sums, vector operations, printed diagnostics, long-width rounding, time/memory and native >4-GiB file-service probes pass. | Whole scientific >4-GiB analysis, combinatorial/integer overflow, aliasing and the remaining general-purpose API are not certified. |
| M09 statsubs | 3 / 143 | Independent unequal-block jackknife oracle, one-block rejection, ordinary/weighted f3 and direct jackknife probe. | F048/F080: invalid trimming/undefined normalized input reaches shared calculations. Every tail/distribution and independently derived trimmed/unweighted variant remains pending. |
| M10 linsubs | 0 / 33 | Separate solver and singular-return regressions pass; no linear solve is used by ordinary f3. | Constrained optimizers, pivots, all singular/nonfinite/ownership and alias cases are outside this audit. |
| M11 mcio | 66 / 127 | Text/packed/transposed/ancestry/PED/BED, gzip, truncation/error cleanup, filtering, input sizes, duplicate-SNP rejection and duplicate-individual direct validator probes. | F050 at the qp3Pop caller; F082 ploidy metadata flow. No full research dataset, complete large-file analysis or exhaustive format/encoding/storage-failure proof. |
| M12 geno | 12 / 27 | Both orientations, byte-exact conversion/round trips, direct tiny/nonaligned dimensions, malformed headers, overflow, read failure cleanup and write failure probes. | All allocator/mapping races, no-assert builds and external mutation contracts remain pending. No prior repaired header/I/O defect was observed in these regressions. |
| M13 mapfile | 0 / 3 | Separate native/Linux map success, missing-file rejection and descriptor lifecycle probes; native offset service crosses 4 GiB. | T05 did **not** rerun the qpWave injection job: its Windows link requires rank/eigen objects absent from this isolated tool set. Earlier evidence remains historical. Allocation failure after mapping and external truncation races remain untested. |
| M14 admutils | 22 / 89 | Population membership/selection, actual genotype access and bit packing, duplicate-ID validator, seeded sampler/physical subset evidence. | F045/F050 are caller omissions; F082 depends on `Indiv.hasxhets`. All record mutators, selection/capacity arithmetic and ownership paths remain pending. |
| M17 qpsubs | 20 / 132 | `f3sc/f3scz/loadaa/getrawcolx`, counts, target het gate, sample weights, block definitions and jackknife; seven oracle families plus all-male X pass. Direct f3 boundary and Fourier regressions retained. | F048, F075, F076, F080, F082 are open. Mixed-X oracle fails. Other estimators, cached statistics, every ploidy/large-count/bounds contract and helper consumers are not certified. |
| M18 egsubs | 1 / 6 | Population-name reading plus separate typed-list capacity and repeated file-close probes pass. | Legacy caller-capacity and all list ownership/error contracts remain independent work. |
| M19 ldsubs | 0 / 12 | Separate diploid LD/empty-count probes pass; ordinary qp3Pop does not calculate LD. | Phased/rare-cell/likelihood/optimization contracts and scientific consumer audits remain pending. |
| M20 regsubs | 0 / 21 | Separate ordinary/singular regression diagnostics pass; ordinary f3 performs no fit. | Logistic/constrained fits, all nonfinite/ownership paths and full downstream scientific callers remain pending. |

## Header and ABI checks

The fresh module inventory maps transitive includes to H01-H03, H09, H12-H14,
H16, H18-H21, H23-H31, H33, H35 and H38-H39. qp3Pop itself also includes stale
upstream declaration/default headers H04 `eigsubs.h`, H10 `globals.h` and
H15 `mcmcpars.h`; their
presence is not proof of active eigen/MCMC modes. All H items retain their own
queue status. Windows LLP64 guards, `admix_long`/offset formatting, binary modes,
`SNP`/`Indiv` layouts and the actual upstream version suffix were reviewed in
the tested dependency paths. F075 concerns a 32-bit accumulator on **both**
LP64 and LLP64. F082 concerns field initialization and ploidy interpretation,
not a difference in C struct layout between the platforms.

No LAPACK/BLAS integer ABI, fast-math, CPU-specific reassociation or scientific
default was changed. Actual Linux qp3Pop dynamic linkage is libc/libm. Windows
runtime dependency discovery copied its real required DLLs; all source/build
hashes and package versions are in T05 evidence. The shared-function probes link
additional library services deliberately; that does not add those operations to
the production qp3Pop calculation.

## Connected executable regressions and propagation

Freshly built `convertf` and `transpose` prepare all input formats and complete
normal/transposed binary round trips. `qp4diff` and `qpF4ratio` ordinary results
and qpF4ratio's overflowing-block rejection pass the shared matrix. The
documented qp3Pop -> `qpBound` workflow produces two bounded-mixture rows,
matching Windows/pristine/current Linux after version/executable metadata.
This is a targeted T21 integration check, not a qpBound audit.

Earlier repaired block-label, packed-header/size/I/O, hash, median, list-close,
singular-diagnostic, numeric/CRLF parser and gzip-cleanup regressions remain
effective in these scopes. No production file was edited, so broader sibling
test suites were not repeatedly rerun without a new change.

F075/F076/F082 propagate through `loadaa/getrawcolx` to possible f-statistic
consumers; use the inventory's reference candidates and actual caller invariants
before asserting reachability. Recheck qpAdm, qpfstats, qpWave and qpDstat's
inbreeding/X paths when repairing those shared contracts. The negative-type
probe does not show that qp3Pop's ordinary valid local type assignment is unsafe.
Missing seed/ID checks and inactive controls in qp3Pop are local omissions, not
regressions in earlier corrected tools. Independent T06/T07/T10/T11/T21 and all
other tool/module/header IDs remain open in their original queue positions.

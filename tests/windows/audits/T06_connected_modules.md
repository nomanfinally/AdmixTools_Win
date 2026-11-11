# T06 connected modules, headers and tools

Status: **scoped review with open findings**, 11 November 2026. Independent M/H
audits remain pending. See [T06](T06_qpF4ratio.md) and its
[evidence](T06_qpF4ratio.evidence.json) for actual failures, hashes, statuses,
builds and environment. Compilation/linkage or earlier evidence is not a pass.

The [corrected-Linux experiment](T06_qpF4ratio.corrections.md) was subsequently
removed from active code following the user's compatibility-only clarification.
See [scope restoration](T06_scope_restoration.md). The original module hashes
and inventory below again describe the active T06 shared-source baseline.

## Dependency and execution boundary

The native link is qpF4ratio, qpsubs, mcio, mapfile, ldsubs, admutils, egsubs,
regsubs and geno, the nine-source nick archive and Windows compatibility/resource
objects. The [compiler inventory](T06_modules.inventory.json) contains **18 shared
modules / 1,102 function declarations**, plus the tool's 10 functions. It records
hashes, transitive headers, warnings and platform directives. Reference candidates
are navigation aids; same-named definitions in separate executables are not
cross-process calls. Warnings alone are not findings.

The active path parses controls, reads genotypes/population rows, selects records,
constructs blocks/counts, evaluates f4 and computes weighted jackknifes. Only
requested limiting invokes permutation code. There is no rank fit, graph fit, LD
regression, MCMC or scientific helper process. Gzip uses the shared input service.
convertf/transpose jobs are validation preparation, not qpF4ratio subprocesses.

Fresh `GCOV_PREFIX` counters include qpF4ratio cases only. They exclude helper
preparation and qp4diff. Counts below are executed functions / Windows compiler
declarations, not branch coverage or a pass. Optimized Linux declaration counts
can differ. Aborting processes may not flush error-branch counters. Independent
shared probes run separately.

| Item | Execution / declarations | Contract checks and source review | Remaining scope / findings |
| --- | ---: | --- | --- |
| M01 win32/compat | Windows only / 25 | Native binary I/O, getopt adapter, backslash temp paths, gzip ownership, sibling argv bytes, process failures/services, PRNG sequences and >4 GiB offsets. PowerShell streams/Tee/cleanup pass. | F044 corrected at the T06 call site. Every Win32 allocation, cancellation, Unicode/long-path/concurrent-temp and injected error path remains independent. |
| M02 strsubs | 24 / 121 | Population line counting/tokenization, open/fatal routing, colons/comments, missing paths; standalone string and legacy-shell probes. Split token versus caller row ownership traced. | Local parser/numlines capacity disagreement causes F083. `nplist*8` also lacks a checked int-product boundary; huge lists were not allocated to reproduce that theoretical limit. Every generic parser/caller remains separate. |
| M03 getpars | 12 / 23 | Scalar/vector syntax/overflow, CRLF macros, includes/loops, line/parameter limits, Windows Unicode quoting/BOM and UTF-16 rejection. Prior shared repairs remain effective. | Tool-specific domain checks are absent (F048/F085); inactive keys can be echoed without an effect. Its parser handle survives until process exit; repeated embedding is not a supported tool mode. Full include/encoding/ownership contracts remain pending. |
| M04 gauss | 0 / 2 | Independent Gaussian/reseed and platform sequence probes. | No Gaussian calculation is part of the estimator. Distribution tails and other consumers remain pending. |
| M05 gds | 1 / 40 | Actual `ranperm` via limiting; independent distribution/sampling bounds and seeds 0/1/77/123/high bit. | Shared sampler correctness does not repair T06's stale index (F084). The tool neither parses nor initializes a seed. Full distribution contracts remain separate. |
| M06 sortit | 6 / 18 | Input sorting/lookups; ordinary equal/empty/vector behavior, median lifetime and fixed-seed order probes. | All equal-key variants, alias/null/capacity boundaries and consumers remain pending. No order changed for T06. |
| M07 xsearch | 8 / 23 | Actual name lookup/duplicate SNPs, extreme hash/bit probes and prior unsigned-arithmetic repairs inspected. | Individual duplicate validation is omitted by the caller (F050). Collision/capacity/ownership coverage is not exhaustive. |
| M08 vsubs | 24 / 257 | Block clears/sums/arithmetic and `asum/vdot` calculation order; independent allele/jackknife oracles and vector/platform probes. | No reassociation/fast-math. Every size, aliasing, nonfinite and integer-vector contract remains pending. |
| M09 statsubs | 3 / 143 | Actual `weightjack/weightjackx`, unequal block weights, zero/one-block rejection and independent ratio/diff jackknifes. Both workspace paths repeat under leak detection. | Caller global-ratio/SE degeneracy remains F080. Other jackknife variants and statistical distribution tails are not T06 modes. |
| M10 linsubs | 0 / 33 | Standalone ordinary/singular solver probes and declaration/ABI/warning review. | The active ratio needs no solver. Full ill-conditioned/nonfinite/numerical/ownership contracts remain separate. |
| M11 mcio | 46 / 127 | Actual text/packed/transposed/ancestry/PED/BED/gzip matrix, headers/truncation, invalid calls, duplicate SNPs, X reader behavior and owned-temp cleanup. | F048 reaches numchrom arithmetic here. Reader-level M-heterozygote filtering does not establish correct countpops X weighting (F087). X format equivalence, real giant input and interrupted/I/O-failure paths remain open. Pristine input defects remain reference differences. |
| M12 geno | 0 / 27 | Real packed transpose/round-trip preparation; separate packing/accessors/header/size/map/full-read/write-error and descriptor-lifetime probes. | No out-of-line function execution counters in the tool-only rerun; helper/shared work must not be attributed to that count. Every allocation, byte-size product and concurrent mutation contract remains pending. |
| M13 mapfile | 0 / 3 | Shared map success/missing-file/descriptor checks, native offset probe beyond 4 GiB, prior failed-map cleanup inspected. | No tool-only out-of-line counters. Separate qpWave forced-map injection needs unrelated rank objects and was omitted. Sparse-offset evidence is not a >4 GiB genotype/mapping audit. |
| M14 admutils | 13 / 89 | Individual/SNP records, genotype access, ignore flags, coordinates/membership; direct indexed-count probe and independent seeded sample probes. | F084 is index construction order, not the permutation algorithm. F050 is missing caller validation. Other record mutators/lifetimes/group capacities/products remain independent. |
| M17 qpsubs | 14 / 132 | `loadindx/loadsnpx/getrawcol/countpops`, map/blocks, `getf4/hfix`, fancy missingness and overlap corrections. Direct Fraction oracle covers NULL/negative sentinels and INT_MAX allele cells. Nineteen full-data oracle cases cover both estimators and numerator/denominator permutations; shared block guards pass. | F087 doubles X calls and ignores ploidy. F084 requires a prefiltered index. `getf4` has no upper-bound argument, but main constructs valid indices/sentinels; hypothetical arbitrary-index misuse is not claimed as a reachable default crash. Other statistic/cache/graph APIs remain pending despite selected FFT probes. |
| M18 egsubs | 0 / 6 | Standalone typed-list/capacity and repeated-close probes pass; declarations/ownership reviewed. | Local `readpopx` belongs to qpF4ratio, not egsubs. Every generic list reader/caller remains separate. |
| M19 ldsubs | 0 / 12 | Standalone ordinary/empty-count LD probes and declaration/ABI/warning review. | LD is not an active ratio mode. Phased/rare-cell/likelihood/optimization and other consumer checks remain pending. |
| M20 regsubs | 0 / 21 | Standalone ordinary/singular regression probes pass after prior repairs; no shared source changed. | The tool performs no fit. Logistic/constrained/nonfinite/ownership APIs and their consumers remain separate. |

The shared matrix has **80 Windows / 78 Linux / 78 ASan** cases; all scoped
verifiers pass. Windows adds native process/service cases; Unix has `/dev/full`.
The selected consumers are qp3Pop, qp4diff, qpF4ratio and transpose. Unrelated
qpAdm/qpfstats/qpWave/qpDpart tools are not claimed to have been re-audited.
The six direct T06 cases additionally cover real ratio/diff allocation cleanup,
bad block indices, zero rows, large counts, NULL/fancy/overlap return contracts,
and raw versus ploidy-aware indexed counts.

## Headers and ABI

The inventory maps transitive local includes to stable H IDs. Global/default,
legacy and nick string/vector/statistics headers remain upstream. Inclusion does
not establish an active MCMC, banking or graph mode. No public structure,
serialized layout, BLAS integer ABI, PRNG, statistical default or header changed.

The Windows forced compatibility header supplies the existing 64-bit offset,
`admix_long` and formatted-I/O contracts. Local result fields use int counts and
double estimates. Unused `int k` receives `admix_long getgenos`, a narrowing
warning without a calculation consumer. Actual huge list/input/block products
are not all proven safe by these small fixtures. Platform probes distinguish
LLP64/LP64 and test offset seeking past 4 GiB. Every H item stays independently
pending.

## Architecture and follow-up

Preserve the shared Windows services and upstream scientific layout. Fix actual
capacity/ownership, domain, selection-order and X-counting contracts with explicit
corrected Linux/Windows evidence. T06 changed no shared production module; its
getopt-only correction has no new scientific caller surface.

Dormant `getrs/islegal/isclade/setabx` have no active caller in supported modes,
consistent with source tracing and zero counters. They retain stale assumptions,
including islegal's 100-element stack array. Bound/remove them only in separately
reviewed cleanup; do not advertise tested banker/tree functionality here.

qp4diff shares f4/count/block/jackknife services and a similar local population
reader. Its ordinary regression passes; `blockname` is ignored. Source similarity
identifies T07 follow-up rather than proving every T06 defect there. Other
countpops users need their own X checks when F087 is corrected. convertf/transpose
were used for real preparation/round trips; their complete audits remain T10/T11.
No module/header checkbox was closed by this scoped review.

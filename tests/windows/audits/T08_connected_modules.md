# T08 connected modules and headers

Scoped review, 12 November 2026; see [T08](T08_qpGraph.md),
[evidence](T08_qpGraph.evidence.json) and [inventory](T08_modules.inventory.json).
No M/H/Q item is closed by a tool-level fixture or syntax scan.

The native link comprises qpGraph, gslqp, qpgsubs, qpsubs, mcio, mapfile, ldsubs,
admutils, egsubs, regsubs, geno, nine nick archive modules, Windows services and
the manifest resource. The compiler inventory scans all **20 shared modules**,
qpGraph, qpfstats and qpreroot: **23 successful syntax scans**, with declarations,
transitive project headers, warnings and reference/call candidates. References
are navigation aids, not proof that every function executes.

| Items | Reviewed/exercised contract | Remaining scope |
| --- | --- | --- |
| M24 qpgsubs; H33 qpsubs | Both graph syntaxes, population/base ordering, paths/ancestral weights, locks/zero constraints, multi-ancestor and two-mixture models, reroot, serialization/DOT, simplify/delete and reload/free. Independently derived edge-weight vectors and pristine output comparisons. F091 changes only the Windows temporary component. | F095 unchecked capacities/operands/variadic diagnostics, F096 leaks and singleton lifecycle. 55/110 functions hit; hash, calctime/IBD/kimf graph services and all graph-edit APIs remain independent. qpfstats/qpff3base/kimf are other direct link consumers; the changed gsimplify path is called by qpreroot, not by their statistical paths. |
| M25 gslqp | Same GSL nmsimplex2 type, step .1, boundary folding, penalty, precision and iteration ceiling. Tree/no-op setup, no optimization, verbose and interior/boundary/two-mixture fits. Independent convex-objective bridge test, byte-exact native/pristine output. | F096 allocation lifecycle. gslnewvals is not called by this qpGraph flow; 4/5 functions hit. Alternate GSL/BLAS versions/CPU dispatches are not certified. |
| M01 compat; H38/H39 | Direct sibling qpfstats execution, argv/path quoting, stdout log and child stderr, native/Unicode/spaced temp paths and owned cleanup. F092 preserves graphcall's upstream ignored-status/copy policy; graphcall=0 branches retain their existing predicates. Native PS and nonzero-child-with-valid-data regression. | F088 damaged gzip and F093 reservation-versus-empty-child-output gap. Other helper callers need independent lifecycle audits. No forced termination/ACL/collision matrix was added; existing T02 evidence is historical, not a substitute. |
| M02 strsubs / M03 getpars | Current parsing, actual scalar/path keys, command echo, parameter precedence, BOM/CRLF/quotes, native temporary path formatting, file/fatal routing and CPU metadata. Main/getopt failures and stdout/Tee are exercised. Unix mkfstats now equals pristine. | F037 and inherited parsing quirks remain. Generic shell/interpreter helpers and all include/vector/number domains remain independent. Parameter handles live until process exit upstream. |
| M04 gauss / M05 gds / M06 sortit / M07 xsearch | Graph initialization, one/two-mixture random trials and seeded cases; default/glibc generator, 8 seeds/800,000 byte-exact outputs, rounding and equal-key ordering. qpfstats label/hash preparation. | F017 inherited hash UB. Distribution families, every tie/collision/capacity and implicit-RNG consumer remain open. No upstream seed/limiting correction was reinstated. |
| M08 vsubs / M09 statsubs / M10 linsubs | Actual covariance/basis algebra, constrained edge solves and GSL callbacks; independent interior [2,3], boundary [0,2.5] and residual 1.5 solver oracles. Score/tail/outlier/fit output exact at printed precision across successful fixtures. | F096 solver leaks, singular/nonfinite/half-score failures. All aliasing, sizes, conditioning and statistical helper contracts are not covered by these small matrices. |
| M11 mcio / M12 geno / M13 mapfile / M14 admutils | Automatic qpfstats reads real text, packed, transposed and gzipped fixtures. Real packed round trips, byte equality, missing files, damaged gzip and limiting/inbreed/allsnps calls. Separate sparse size/seek/map >4 GiB probe. | F088; actual huge genotype/count products, every format/mapping/ACL failure and independent X/ploidy correctness remain with T02/M11. Explicit-fstats qpGraph bypasses genotypes, so linked code is not falsely counted as direct tool execution. |
| M17 qpsubs | fstats population/header/base parsing and load, covariance symmetries, graph basis construction, bad-pair/regularization controls. Empty/short/missing/NaN files and all generated fstats bytes retained. qpfstats computes the automatic input. | Empty-fstats NULL base, fixed population capacities, incomplete malformed/covariance validation and all unrelated estimators remain inherited/open. |
| M18 egsubs / M19 ldsubs / M20 regsubs | Link/header/platform review and calls reached through automatic qpfstats data/block preparation. | No independent LD-decay or regression analysis is exposed by qpGraph. Full standalone contracts stay pending. |

Project header H IDs are mapped in the inventory. The admix_types long/format
adapters preserve 64-bit LP64 counters on Windows LLP64; BLAS/GSL integer ABIs
remain 32-bit. The two qpGraph long counters only control calls/debug paths.
No serialized layout, numerical constant/table, precision or PRNG changed.
Globals/mcmcpars/badpairs inclusion does not establish a working MCMC mode.

qpfstats is the runtime scientific helper. convertf/transpose are preparation
tools, and qpreroot is an explicitly exercised related executable. Optional
qpreroot rendering produced environment-dependent diagnostics; no renderer
installation or PDF parity was inferred. T08 does not close T09, any installed
interpreter helper, or graph services used by kimf/qpff3base beyond these calls.

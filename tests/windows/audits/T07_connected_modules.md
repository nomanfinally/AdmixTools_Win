# T07 connected modules and headers

Scoped review, 12 November 2026. See [T07](T07_qp4diff.md) and
[machine evidence](T07_qp4diff.evidence.json). Independent M/H items remain
pending. A compiler declaration or archive member is not runtime coverage.

The native link contains qp4diff, qpsubs, mcio, mapfile, ldsubs, admutils,
egsubs, regsubs, geno, nine nick archive modules, and the Windows compatibility
and resource objects. The [compiler inventory](T07_modules.inventory.json)
records function declarations, call/reference candidates, transitive headers,
hashes, warnings and platform directives for the tool and all 18 shared modules.
All 19 syntax scans succeed; warnings were inspected without treating their
count as a defect count. Relevant width changes preserve LP64 long using
admix_long on LLP64; size_t formatting and stat/lseek adapters remain shared.

| Items | Active contract and new evidence | Remaining scope |
| --- | --- | --- |
| M01 compat; H38/H39 | Native CRT binary mode; Unicode/long-path manifest; getopt adapter; owned zlib temporaries; default/glibc RNG and offsets. Direct PS/Tee/stream/293-character-temp checks, 800,000 RNG outputs and 4 GiB sparse map/seek pass. | F088 damaged-gzip acceptance/exit gap is open. F089 undefined Z spelling is open. All process helpers, allocation/collision/policy/error combinations are not certified. No estimator helper subprocess is used. |
| M02 strsubs | Population row counting/splitting, colons/comments, file/fatal routing, temporary naming and CPU metadata. Long rows/comments reproduce F083 and Windows backslash temp paths pass. | Whole-line capacity, every generic string helper, shell helper, allocation and ownership contract remain independent. Temporary cleanup on observed native reader errors passes. |
| M03 getpars | All parsed T07 scalar/path parameters, precedence, echo, BOM/CRLF macro and Windows quoting; partial numbers/inactive keys retain pristine behavior. | F048/F051/F073 remain inherited. The parameter handle survives until process exit. General include/vector/parser boundaries are not newly certified by T07. |
| M04 gauss / M05 gds | Sampling via setplimit reaches ranperm; platform RNG probe checks 8 seeds including high-bit seeds, rounding and repeatable binary output. | No Gaussian or scientific sampling mode beyond population limiting. Matching RNG does not repair stale analysis indices (F084). Other distributions remain independent. |
| M06 sortit / M07 xsearch | Metadata sorting/lookups, duplicate SNP/individual cases, equal-key platform order. Port tie-order/64-bit type changes reviewed. | F017 signed-shift/overflow remains in restored hash bodies; sanitizer diagnostics are retained. Other sort/hash capacities, collision/lifetime variants and long keys are not complete. |
| M08 vsubs / M09 statsubs | Allele/block accumulation and actual weightjack/weightjackx; 11 independent full-data oracles cover both estimators, 24 quartet orders, missing supports, covariance corrections and unequal weights. | No tolerance/reassociation. Zero SE remains undefined, and all vector alias/size/nonfinite/distribution contracts remain separate. |
| M10 linsubs | Linked through nick; declarations and numerical ABI reviewed. | No linear solve in the active estimator. Standalone solver APIs are not certified by compilation. |
| M11 mcio | Real text/packed/transposed/ancestry/PED/BED fixtures, gzip success/errors/concatenation, truncation, duplicate IDs and input failures. | F088 and inherited gzip PLINK extension dispatch, F048 numchrom overflow and F050 duplicate-ID acceptance remain. Male heterozygote reader filtering does not establish sex-aware population counts. |
| M12 geno / M13 mapfile | Real transpose/packed round trips, binary bytes, reader failures; separate platform sparse mapping beyond 4 GiB. Width/mapping API guards and file lifecycle source reviewed. | Helper preparation is not attributed to qp4diff runtime. Real giant genotype arithmetic, forced-map failure, concurrent mutation and all allocation/header contracts remain independent. |
| M14 admutils | Record/group membership, genotype access, ignore flags, instem paths, default random limiting, physical subset comparison. | F084 constructs indices before limiting. No sample-selection reorder, new seed parsing or ploidy correction was introduced. |
| M17 qpsubs | loadindx/loadsnpx/countpops, map/block setup, getf4/hfix, both missingness policies, weighted jackknife. Fraction-based direct oracle tests ordinary/repeated/NULL and INT_MAX cells. Direct bad block/zero row probes preserve current returns/fatals. | F087 shared X-counting concern remains. countpops uses two alleles/call; T07 X matrix is reference compatibility, not independent sex-aware correctness. Arbitrary invalid positive population indices have no normal main path and are not claimed as a reproduced tool defect. |
| M18 egsubs / M19 ldsubs / M20 regsubs | Link/declaration/header/platform-diff inspection. Local readpopx belongs to qp4diff. | No egsubs population reader, LD estimator or regression fitter is an exposed qp4diff mode. Their full independent contracts remain pending. |

Headers are mapped to existing H IDs in the inventory. admix_platform keeps
`470` on Unix and `470.w` on Windows; admix_types, mcio/mapfile declarations and
nick format macros preserve widths consistently. No header, serialized format,
scientific table, PRNG, BLAS integer ABI or public structure changed during T07.
Unused mcmcpars/global declarations do not imply an active MCMC/banker mode.

Coverage reaches main, readcommands, readpopx, doq4diff, doq4diffx and usage.
getrs/islegal/isclade/setabx/doq4ratdiff are dormant legacy functions. islegal's
100-element stack array is a static maintenance concern, not an exposed T07
runtime mode. Broad cleanup should be separated from the port baseline.

convertf/transpose are tested preparation tools, with exact bytes/round trips;
qpDstat, qp3Pop and qpF4ratio have exact normalized default-stream regressions.
No production shared module changed, so this audit creates no new scientific
caller modification. The open shared gzip deviation requires cross-consumer
regressions before changing that service. Old repaired-baseline shared probes
did not compile and are not reused as passing evidence. No M/H/Q item is closed.

# T06 qpF4ratio

Status: **reviewed with open defects**, 11 November 2026. This is not a tool
pass or full-suite parity certification. One Windows presentation regression
was corrected. Nine inherited finding groups remain open in this tool.

Current scope: the user clarified that inherited Linux bugs must remain deferred.
The [scope restoration](T06_scope_restoration.md) removes the subsequent
upstream-bug repairs while retaining the Windows getopt fix. The original
findings and comparisons below remain applicable; the correction experiment is
historical and is not the active compatibility baseline.

Baseline: pristine upstream `67bc219174a109951a9434e0a383ec464fb140ee` from the
local Git object database. Working HEAD: `ecbed635d74d89908b53d21f5cf0caa9d778a50d`,
on the pre-existing `audit-t03-qpwave` topic branch. The initial worktree was
clean. No branch/history rewrite, commit, push, release or installed-bin
replacement was performed. The GitHub page could not be fetched; source
comparisons use the pinned local objects, not an inferred current web version.

[Machine evidence](T06_qpF4ratio.evidence.json) records source, executable,
input and stream hashes, complete statuses, build settings, scientific rows,
independent oracle answers, native checks, coverage and differences.
[Connected-module review](T06_connected_modules.md) and the
[compiler inventory](T06_modules.inventory.json) distinguish actual execution
from linked or dormant code. Independent M/H/Q audits remain pending.

## Result

- Fresh isolated native Windows, pristine Linux, current Linux, ASan/UBSan and
  coverage matrices each completed **131 cases**. These contain expected
  failures and reproduced bugs; completion is not a passing result.
- **76 jointly successful cases with finite scientific rows** agree exactly at
  printed precision between Windows and current Linux (matrix counts include
  the connected qp4diff regressions). Two further cases agree
  on nonfinite rows. `same-contrast` differs in the sign of NaN on Linux/Windows;
  that difference is retained, not normalized away. Among current/pristine Linux
  jointly successful cases, all **73 finite** and three nonfinite result cases
  agree. Agreement includes defective controls and X results; it does not prove
  those results correct.
- **15/19 independent oracle cases pass** on every build. These cover ordinary
  ratios, reciprocal ratios, f2/f3 overlap corrections, constant-NULL denominators,
  missing-data/fancyf4 rules, 24 numerator and 24 denominator permutations,
  unequal-block jackknifing, and `diffmode` including different SNP support in
  its two component ratios. Female-only X and distinct-population male X pass.
  Four X cases fail on Windows and pristine/current Linux: mixed, unknown sex,
  mixed f2 and male f2 (F087).
- Full normalized terminal/status/file comparisons are **89/131** Windows/current
  Linux, **115/131** current/pristine, **126/131** current/ASan and **129/131**
  current/coverage. Raw comparison JSON/diffs retain every other difference.
  These are exact comparisons, not tolerance-based scores.
- Shared checks: **80 Windows / 78 Linux / 78 ASan** cases pass their scoped
  verifiers. Six direct production-function probes pass on each platform;
  the sanitizer probe enables leak detection and repeats both ratio workspace
  lifetimes 16 times. Native PowerShell direct invocation, separate streams,
  `Tee-Object`, gzip, a working/parameter path with spaces and native temporary
  backslashes pass. Packed genotype transpose round trips are byte-exact.
- Fresh counters restricted to qpF4ratio itself record **6/10 functions,
  310/379 executable lines and 156/232 branches**. The four unexecuted local
  functions are dormant legacy helpers. Error processes that abort may not flush
  counters. This is explicitly not 100% branch or independent module coverage.

## Execution contract and tested modes

`main -> readcommands -> getsnps/getindivs/getgenos -> chromosome selection ->
numlines/readpopx -> population/index construction -> setplimit/loadsnpx ->
setblocksz -> countpops -> doq4rat[/doq4ratdiff] -> getf4/hfix -> weightjack`.
The ordinary path does not invoke qpfstats, a rank fitter, a graph optimizer,
or an interpreter helper. Gzip uses the shared platform decompression service.

| Surface | Actual contract and checks |
| --- | --- |
| CLI | `-h`, `-p`, `-v`, `-V`; no arguments, missing operand/file, invalid option and combined `-v -p` tested. Version is upstream `2010`, Windows `2010.w`. The inherited misleading version-exit behavior remains F051. |
| Ratio input | Eight population names per row; colons/commas are separators, comments/blanks are skipped, extra columns are ignored. Known populations, missing populations, empty/short/long lines, long comments and repeated populations tested. `NULL` in any denominator slot makes that entire f4 equal 1 through `getf4`'s negative-index sentinel; it is not partial population omission. NULL in the numerator rejects. |
| Ordinary estimator | Per-SNP numerator and denominator f4 on joint eligible sites, signed global ratio, weighted delete-block jackknife. The upstream `1e-10` delete-denominator term, computation order, printed precision, SNP count and unconditional `zzblock:` output are preserved. Zero denominators remain F080. |
| `diffmode: YES` | The first half of rows pairs with the second half. It computes **alpha A + alpha B - 1**, not alpha A minus alpha B. The component rows use their own valid sites; the combined estimator uses sites shared by both ratios. Two/four rows and unequal missingness are checked. Odd/single rows and a nonboolean value expose F085. |
| `fancyf4` | Default YES permits zero f4 when an observed contrast pair is equal even if the other pair has missing data; NO requires complete populations. Both have independent oracles. Repeated cross-pair populations use the shared sampling correction. |
| Selection | `chrom`, `noxdata`, `xdata`, custom `numchrom`, explicit X, no surviving SNPs, bad-SNP list, positive/invalid block sizes, forced physical distance and zero-map fallback tested. `xdata` and explicit X override the default X exclusion as upstream does. Population size limits are defective (F084). |
| Blocks | Default map blocks and explicit block files; unequal, negative, sparse, malformed, excessive/INT_MAX, missing and duplicate labels checked. Existing shared label/dimension guards remain effective. Repeated definitions currently override earlier definitions; this accepted behavior is retained as an observation, not declared a newly fixed defect. One/two SNPs and a single usable block reject through the existing jackknife guard. |
| Genotype inputs | EIGENSTRAT, packed normal/transposed, ancestry records, PED/BED; gzip for all six, concatenated members, corrupt/truncated/CRC and reader-fatal gzip; absent, empty, malformed/truncated genotype/metadata files and duplicate IDs tested. X oracle coverage is text input; X conversion/format equivalence is not certified. |
| Output and controls | Both streams/statuses and all `result:`, `q4rat A:`, `q4rat B:`, `diff:` rows retained. `output:`/`outputname:` are unsafe empty-file side effects (F086). Parsed `nostatslim` has no analysis effect. `seed`, `inbreed`, `jackweight` and `jackquart` are not parsed controls here, despite stale globals or support in other tools. No new parameter support was invented. |
| Windows | Native PE x86-64 executable with shared CRT/binary-I/O, offset and process compatibility services. PowerShell 5.1 AMD64, paths with spaces/Unicode/#, forward-slash inputs, BOM, CRLF substitution, rejected UTF-16, gzip cleanup and native backslash temp display tested. Extended Unicode/BOM parser acceptance is Windows-specific. |
| Connected tools | Actual convertf/transpose preparation, qp4diff ordinary behavior and its ignored `blockname` control, qp3Pop ordinary/shared block rejection, and qpF4ratio shared block rejection checked. These targeted regressions do not close T05/T07 or conversion-tool audits. |

## Findings

Except F044 below, all findings are **open for T06**. Reused F IDs mean another
occurrence of the same finding class; earlier tools' scoped corrections remain
valid. Case names refer to the authoritative matrices; run `qpF4ratio[.exe] -p par`
from the named case directory. The raw manifest contains the actual exit code.

| ID / severity / classification | Reproducer, evidence and cause | Smallest repair direction |
| --- | --- | --- |
| **F044 / medium / Windows regression, corrected** | `cli-invalid-option` and `cli-missing-value` originally used MinGW wording (`unknown option -- z`, unquoted `p`); pristine Linux uses `invalid option -- 'z'` and quoted `'p'`. Local raw `getopt` bypassed the existing Windows adapter. | Four guarded lines select `admix_getopt` on Windows, leaving raw Unix getopt intact. Both corrected stderr diagnostics match Linux after executable suffix normalization. No algorithm, default, stream routing or fatal behavior changed. |
| **F048 / high / inherited input/UB** | `zero-blocksize`, `negative-blocksize`, `nan-blocksize`, `inf-blocksize` return success with scientific results. `numchrom-intmax` reaches signed `numchrom+1` overflow in main and mcio under UBSan. Local domain checks are absent; rejecting later with `no valid snps` does not undo UB. | Validate finite positive block size and representable positive `numchrom` before genotype loading. Keep valid block construction and numerical order unchanged. Recheck shared readers and callers using other chromosome counts. |
| **F050 / medium / inherited input integrity** | `duplicate-ind` exits zero on native/pristine/current builds. The existing `check_duplicate_individuals` call is missing before genotype loading. Duplicate SNPs reject separately. | Invoke the existing duplicate-ID validator before any genotype/hash/mapping work; regress all input formats and selected populations. |
| **F051 / medium / inherited interface** | `cli-version` prints `version: 2010[.w]`, stderr `no parameters`, then a second version banner, despite help saying version-and-exit. With `-v -p`, analysis continues. `nostatslim` is parsed/clamped but never used in the estimator. | Choose/document an explicit upstream-bug repair for truthful version/unsupported-control behavior, using the earlier tools' scoped approach. Do not change historical behavior silently as a Windows formatting fix. |
| **F080 / high / inherited degenerate estimator** | `zero-bottom` and `constant` return success with alpha NaN and SD 0; `same-contrast` emits zero alpha/SD and undefined Z. `doq4rat` and `doq4ratdiff` divide global sums without finite/nonzero denominator validation. Printed NaN sign differs by CRT. | Reject an undefined global ratio before jackknife/result output; preserve legitimate negative f4 denominators and upstream delete-block epsilon. Define zero-SE reporting explicitly rather than silently changing estimates or removing result lines from comparisons. |
| **F083 / high / inherited heap corruption** | `long-ratios` and `long-comment` corrupt the native heap (`0xC0000374`); current Linux aborts, and ASan reports a heap-buffer-overflow in `readpopx`. `numlines` counts physical lines using a 10,000-byte buffer; local `readpopx` splits them into 511-byte fragments and writes more row pointers than were allocated. A long comment's continuation can become a data row. The pinned local source has the same defect. | Give the parser one bounded row-capacity contract and consistent whole-line reading/counting; check count/product limits and read failures. Reuse an appropriate shared reader only after checking its own capacity/error behavior. Preserve valid colon/comment/extra-column semantics. Apply separate reviewed fixes to sibling copies, not a speculative parser rewrite across tools. |
| **F084 / high / inherited scientific control** | `limit-3`/`limit-1` print the same full-sample result as `default`: `-34.058028 24.728619 -1.377 2200`. A physically reduced three-per-population fixture gives `-13.634856 13.062440 -1.044 2200`. Main constructs `xindex`/`xtypes`/`nrows` before `setplimit`; `countpops/getrawcol` consume that stale index and never consult updated ignore flags. Limiting can still remove SNPs via `loadsnpx`, making the control inconsistent rather than simply a harmless no-op. `seed: 77/123` is not parsed and no seeding call occurs. | Select individuals before constructing the analysis index and population counts; verify a physically identical subset and intended RNG/default policy on corrected Linux and Windows. Seed support needs an explicit upstream-compatible decision; do not introduce a new PRNG, seed default or silent statistical change. |
| **F085 / medium / inherited input/result loss** | `diff-odd` silently drops the final row, `diff-single` exits zero without results, and `diff-invalid` (`diffmode: 2`) bypasses both branches and exits zero. The half-list loop and equality tests have no preconditions. | Require a boolean mode and an even, nonzero paired row count before analysis/output side effects. Preserve first-half/second-half pairing and the existing sum-minus-one statistic. |
| **F086 / high / inherited output data loss** | `output` and `outputname` start with a 25-byte sentinel file; both truncate it to **0 bytes**, exit zero and print scientific results only to stdout. `openit(...,"w")` is called before data validation, but `ofile` is never written or closed explicitly. | Keep stdout as the documented result interface; reject the inactive output controls before opening anything, or implement a separately reviewed truthful file-output contract. Preserve existing files on rejection. PowerShell redirection is the tested current workflow. |
| **F087 / high / inherited X-ploidy scientific defect** | Mixed X oracle expected alpha/SD/Z `-68.973304 110.565097 -0.624`; actual `142.710231 55.838273 2.556` on Windows/pristine/current Linux. Homozygous all-male repeated-population f2 expected `0.462744 1.240413 0.373`; actual `1.707292 2.954267 0.578`. Unknown sex also fails. `countpops` adds two alleles per indexed call, ignoring sex/ploidy; reader-level male heterozygote filtering does not fix mixed-sex weighting or repeated-population `hfix` sample counts. | Establish and apply the declared F-diploid/M-U-haploid contract at this counting path, including repeated-population correction denominators and insufficient haploid counts. Regress X across text/packed/PED readers and other countpops consumers. This is a different path from the repaired T05 `getrawcolx` defect F082; its correction will intentionally change current/pristine X numbers. |

Partial-NULL denominator semantics, extra population columns and duplicate block
definitions are retained observations. There is insufficient evidence to label
every permissive upstream input convention a port bug. Warning-only candidates
are likewise not promoted to verified findings.

## Port architecture and presentation

The port arrangement is appropriate for a direct compatibility baseline: one
native executable, the upstream source layout, a conditional suffix, and shared
Windows services. No new dispatcher, wrapper, output format, PRNG or optimization
is needed. The four-line getopt correction uses that existing boundary.

The inherited scientific executable has weak ownership/capacity contracts:
pre-counted fixed-buffer list parsing, a selection/index ordering bug, duplicated
legacy helpers, process-global state, and unused workspaces/globals. In each
ratio routine `w1/w2/ww` are allocated/freed but unused. Main narrows the
`getgenos` count into unused `int k`; no tested numerical result depends on this
assignment. These are focused maintenance candidates, not grounds for a broad
scientific refactor. Dormant `getrs/islegal/isclade/setabx` are not active modes;
for example `islegal` retains the legacy 100-population stack-array assumption.
Do not mistake same-named functions in separate executables for runtime calls
into this executable.

Windows presentation should continue matching upstream, including `zzblock:`
lines, spacing/precision, signed results and stderr help. Replacing those with a
new progress UI or hiding diagnostic/result lines would violate this port's
contract. The Windows usage documentation now explains the real diff statistic,
Morgans for block lengths, safe stdout redirection and confirmed limitations.

## Build, comparison rules and limits

Windows: MSYS2 UCRT64 GCC 16.2.0, x86-64/LLP64, `-O2` production and `-O3`
nick library, `-ffp-contract=off -fno-fast-math`, 64-bit offsets, shared MinGW
stdio compatibility and an 8 MiB reserved stack. Linux: Ubuntu GCC 15.2.0,
x86-64/LP64, matching optimization/order flags. GSL is 2.8; Windows OpenBLAS is
0.3.34 and Linux OpenBLAS is 0.3.32. Windows zlib headers are 1.4, Linux zlib
package `1:1.3.dfsg+really1.3.1-1ubuntu3.2`. The recorded `ldd` for Linux qpF4ratio
contains libc/libm only: the ordinary ratio is not a BLAS/GSL calculation.
Dependency DLL names/hashes and complete compiler/link commands are retained.
`OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1`, `OPENBLAS_CORETYPE=NEHALEM`, `LC_ALL=C`.
The fixture generator has fixed seed 1907; qpF4ratio itself does not parse a
seed control. No fast-math, reassociation or tolerance increase was introduced.

The comparison helper substitutes only executable `.exe`, requested `.w`,
CRLF, existing CPU/memory/address metadata and owned gzip temporary operands/
quotation. It does not remove scientific rows, debug block lines or normalize
NaN signs. Actual error statuses remain different (Unix SIGABRT/-6, Windows
fatal fast-fail/exit codes); they are recorded. Absolute data paths, BOM/quoted
Unicode Windows input extensions, sanitizer diagnostics, known pristine parser/
gzip defects and scientific nonfinite differences remain visible in raw diffs.
Converted text input line endings can differ by platform; underlying main
fixtures and binary genotype bytes are hashed and binary round trips are exact.

The before/after Windows CLI matrices have **122/126 exact full comparisons**,
with **no scientific-row changes**. The four stream differences are the two
corrected diagnostics and two absolute fixture-path values. The final expanded
131-case matrices supersede the smaller diagnostic runs. Interrupted
`complete-*` runs have no completed manifest and are not evidence of completion.

No actual >4 GiB genotype dataset, Windows fault-injected map allocation,
interrupted decompressor, file mutation during mapping, exhaustive long-path
matrix, native Windows sanitizer run, macOS build or full research dataset was
tested here. Separate shared offset probes cross 4 GiB; that is not proof of
every genotype size/product boundary. Native mapping-failure injection was
omitted because the reused qpWave probe needs unrelated rank objects absent from
this tool set. Detailed independent module/header contracts remain open.

Raw Windows evidence is under `validation-results/hard-check/T06/`; final Linux
runs are `/home/user/admixtools-t06-final/final-{pristine,linux,asan}` and
`/home/user/admixtools-t06/final-coverage`. A portable `linux-evidence.tar.gz`
archive and its SHA-256 are recorded in the machine evidence. The validated
CLI-fixed executable is `validation-results/hard-check/T06/builds/snapshot/bin/qpF4ratio.exe`;
the existing installed `bin/` was left intact. Reproduction commands are in
[the Windows test guide](../README.md#t06-qpf4ratio).

T06 remains unchecked in the hard-audit queue. Correct the nine inherited groups
with explicit corrected-reference evidence, then close remaining applicable
coverage before considering a pass. T04's earlier independent coverage work and
other tools/modules retain their own queue status.

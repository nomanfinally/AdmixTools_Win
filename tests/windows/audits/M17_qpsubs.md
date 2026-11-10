# M17: Shared f-statistic and block code — independent review

Follow-up: [requested T04 repairs](T04_qpDstat.corrections.md) correct the
recorded defects in their reproduced scopes; current source hashes and regression
evidence are linked there. The review below describes the original snapshot.
Independent module/header completion remains pending.

Status: **reviewed; independent contract coverage incomplete; not passed**.
Date: 10 November 2026. No production repair was made.

## Contract and source

`src/qpsubs.c`; SHA-256 `4a3ea1f309c0dc0274fa051002246b76bc7232efe60383b99d999894b7568b20`.
Counts including X ploidy, block definitions/bounds, weighted/Fourier jackknife, selected cached-fstats and automatic qpfstats helper paths.

The pinned upstream and current port baseline, actual build commands, dependency
versions/ABI, environments, raw per-case statuses and archive hash are in
[T04 evidence](T04_qpDstat.evidence.json). Caller/reference candidates and every
compiler-recognized function are in [the function inventory](T04_modules.inventory.json).
Archive membership/reference matches do not establish runtime reachability.

Header closure: `H01` src/admutils.h, `H02` src/badpairs.h, `H03` src/egsubs.h, `H14` src/mcio.h, `H16` src/nicklib.h, `H18` src/nicksrc/admix_platform.h, `H19` src/nicksrc/admix_types.h, `H20` src/nicksrc/getpars.h, `H21` src/nicksrc/linsubs.h, `H24` src/nicksrc/ranmath.h, `H25` src/nicksrc/sortit.h, `H26` src/nicksrc/statsubs.h, `H27` src/nicksrc/strsubs.h, `H29` src/nicksrc/vsubs.h, `H30` src/nicksrc/xsearch.h, `H33` src/qpsubs.h, `H35` src/regsubs.h.
These headers compile in their real production contexts; standalone header
self-containment, every default/table and every inactive platform branch are
not thereby certified. H items remain open.

## Recorded checks

| Contract check | Evidence and limit |
| --- | --- |
| Ordinary and numerical behavior | Direct cases `M17-fourier-0`, `M17-fourier-1`, `M17-fourier-2`, `M17-fourier-5`, `M17-fourier-12`, `M17-fourier-32`; ordinary/mode consumers in T04. Exact output comparison retains discrepancies. |
| Results, streams, files and exits | All raw stdout/stderr/statuses retained; RNG stdout is compared as binary bytes, packed files by SHA-256. OS abort codes are retained. No scientific tolerances. |
| Boundary/malformed input | Direct boundary cases plus T04 input/block/chromosome/format matrix. This is not exhaustive for unexecuted functions. |
| RNG and calculation order | Fixed fresh-process seeds, single-thread dependencies, no fast-math/reassociation; no algorithm change. For non-random functions this row applies only to their random-dependent callers. |
| Widths, ABI and large offsets | Native 64-bit build, 64-bit port offset type, 32-bit BLAS integers; >4-GiB service probe and ordinary genotype round trips. No end-to-end >4-GiB scientific run. |
| Paths, helpers and ownership | Native PowerShell/path/gzip matrix, shared qpWave helper regressions and relevant direct probes. No filesystem/process behavior is inferred for pure numerical functions. |
| Memory and lifetime | Linux ASan/UBSan, selected leak detection, native Windows ordinary/failure probes. First-failure aborts and missing Windows MSan/ASan limit conclusions. |
| Non-Windows and affected callers | Pristine Linux and current Linux builds, targeted sibling cases; macOS not executed. Caller tool IDs retain their independent audit status. |

## Coverage, findings and closure

42/132 Windows-inventory function names executed in the instrumented Linux run. Platform/compiler conditionals can change this denominator.
Compiler warning inventory: 569 warnings under the recorded
extra review flags. Warnings alone are not findings or passes.

For findings, severity, reproducer, platform behavior and proposed repairs, see
[the T04 finding register](T04_qpDstat.md#findings). Existing corrected findings
retain their original IDs and scoped historical status.

**Remaining:** The full 132-function shared surface is not certified. Fourier is unsafe; cached/helper regression evidence does not validate every estimator or every caller.

Functions without a recorded positive Linux execution count:
`fstats_copy`, `fstats_child`, `qpfstats_helper`, `printsc`, `settsc`, `getpdata`, `gethscore`, `getrscore`, `qhdiff`, `qcorr`, `getcolx`, `loadxdataind`, `fixxrow`, `dofancy`, `vadjust`, `yll`, `calcmean`, `setmiss`, `setfvecs`, `countpopsr`, `fixrho`, `printdiag`, `ridoutlier`, `addoutersym`, `symit`, `divcol`, `f3y`, `f2scz`, `f2sc`, `getcntpop`, `finfo`, `f4yx`, `f4y`, `fstcoly`, `dohzg`, `corrwjack`, `crho`, `setbcols`, `doadmlin`, `dof3`, `bump2`, `bump3`, `dump2`, `dump3`, `dof4`, `bump4x`, `bump4`, `dump4`, `map4x`, `dofstnum`, `wjackest`, `ndfst5`, `regestit`, `countg`, `dohzgjack`, `f3yyx`, `f3yy`, `estmix`, `ff3val`, `printnorm`, `fstcolinb`, `doinbreed`, `calchetinbreed`, `calcndinbreed`, `printaa`, `getsampnum`, `oldf3yyx`, `hfix`, `getabbababa`, `gethtest`, `gethest`, `getfreq`, `getaax`, `fstats2eglist`, `dumpfstats`, `getegnum`, `geteffblocks`, `readfstats`, `loadfstatsx`, `loadfstats`, `get4`, `getbco`, `mkcoeffs`, `vv2ww`, `getbasepop`, `sw2`, `sw`, `swx`, `fstats2popl`, `setvv`

No module/header is closed by the T04 tool review. Completing the remaining
contracts requires additional evidence; these limitations are not a clean pass.

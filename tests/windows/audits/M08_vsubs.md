# M08: Vectors and diagnostics — independent review

Follow-up: [requested T04 repairs](T04_qpDstat.corrections.md) correct the
recorded defects in their reproduced scopes; current source hashes and regression
evidence are linked there. The review below describes the original snapshot.
Independent module/header completion remains pending.

Status: **reviewed; independent contract coverage incomplete; not passed**.
Date: 10 November 2026. No production repair was made.

## Contract and source

`src/nicksrc/vsubs.c`; SHA-256 `63be25e4209f80ede8516a78133a1a88ee7c2fd93f260ce27b46e35d88995d78`.
Long-width rounding above 32 bits, arithmetic, sums/dots, matrix print diagnostics and memory/timing consumers.

The pinned upstream and current port baseline, actual build commands, dependency
versions/ABI, environments, raw per-case statuses and archive hash are in
[T04 evidence](T04_qpDstat.evidence.json). Caller/reference candidates and every
compiler-recognized function are in [the function inventory](T04_modules.inventory.json).
Archive membership/reference matches do not establish runtime reachability.

Header closure: `H19` src/nicksrc/admix_types.h, `H27` src/nicksrc/strsubs.h, `H29` src/nicksrc/vsubs.h.
These headers compile in their real production contexts; standalone header
self-containment, every default/table and every inactive platform branch are
not thereby certified. H items remain open.

## Recorded checks

| Contract check | Evidence and limit |
| --- | --- |
| Ordinary and numerical behavior | Direct cases `M08-vector`; ordinary/mode consumers in T04. Exact output comparison retains discrepancies. |
| Results, streams, files and exits | All raw stdout/stderr/statuses retained; RNG stdout is compared as binary bytes, packed files by SHA-256. OS abort codes are retained. No scientific tolerances. |
| Boundary/malformed input | Direct boundary cases plus T04 input/block/chromosome/format matrix. This is not exhaustive for unexecuted functions. |
| RNG and calculation order | Fixed fresh-process seeds, single-thread dependencies, no fast-math/reassociation; no algorithm change. For non-random functions this row applies only to their random-dependent callers. |
| Widths, ABI and large offsets | Native 64-bit build, 64-bit port offset type, 32-bit BLAS integers; >4-GiB service probe and ordinary genotype round trips. No end-to-end >4-GiB scientific run. |
| Paths, helpers and ownership | Native PowerShell/path/gzip matrix, shared qpWave helper regressions and relevant direct probes. No filesystem/process behavior is inferred for pure numerical functions. |
| Memory and lifetime | Linux ASan/UBSan, selected leak detection, native Windows ordinary/failure probes. First-failure aborts and missing Windows MSan/ASan limit conclusions. |
| Non-Windows and affected callers | Pristine Linux and current Linux builds, targeted sibling cases; macOS not executed. Caller tool IDs retain their independent audit status. |

## Coverage, findings and closure

70/257 Windows-inventory function names executed in the instrumented Linux run. Platform/compiler conditionals can change this denominator.
Compiler warning inventory: 69 warnings under the recorded
extra review flags. Warnings alone are not findings or passes.

For findings, severity, reproducer, platform behavior and proposed repairs, see
[the T04 finding register](T04_qpDstat.md#findings). Existing corrected findings
retain their original IDs and scoped historical status.

**Remaining:** Many generic vector/integer/combinatorial functions remain unexercised; warnings are navigation evidence, not accepted proof of correctness.

Functions without a recorded positive Linux execution count:
`vinvert`, `vlog2`, `vexp`, `cpzero`, `ivvm`, `ivsp`, `ivst`, `ivvt`, `lvclear`, `lvzero`, `clip`, `ivclip`, `iclip`, `ivmaxmin`, `minivec`, `maxivec`, `lvlmaxmin`, `corrx`, `variance`, `setdiag`, `copyarrp`, `revarr`, `revlarr`, `revuiarr`, `reviarr`, `copylarr`, `dpermute`, `ipermute`, `multperm`, `dppermute`, `ippermute`, `longsum`, `idot`, `iprod`, `aprod`, `countcat`, `rowsum`, `colsum`, `rrsum`, `ccsum`, `printmatfile`, `printmatwfile`, `printmatx`, `printmat0`, `printmatwxfile`, `printmatw0xfile`, `printmatw0`, `printmatl`, `printmatlx`, `printmatlfile`, `printmatwlxfile`, `printmatlxfile`, `printmatwlfile`, `printmatwlx`, `printmatwf`, `printmatw2D`, `printmat2D`, `printmatl2D`, `int2c`, `floatit`, `printimatwfile`, `printimatw`, `printimatxfile`, `printimatx`, `printimatfile`, `printimat2D`, `printimatl2D`, `printimat1x`, `printimat1`, `printimatlfile`, `printimatl`, `printimatlx`, `printstringf`, `printstringbasepos`, `printstring`, `rndit`, `findbin`, `findfirstl`, `findfirstu`, `findlastu`, `findlast`, `binsearch`, `NPlog2`, `logfac`, `logbino`, `loghprob`, `hprobv`, `log2fac`, `addlogv`, `addlog`, `sublog`, `logsum`, `vlsum`, `ipow2`, `pow10`, `vpow10`, `vlog10`, `initarray_2Dlong`, `initarray_3Dlong`, `free2Dlong`, `free3Dlong`, `free_darray`, `free_iarray`, `initarray_2Dlongdouble`, `lclear2D`, `free2Dlongdouble`, `outer`, `subouter`, `addtensor`, `bal2`, `logmultinom`, `flipiarr`, `fliparr`, `vcompl`, `stripit`, `istripit`, `cstripit`, `mapit`, `ifall`, `hlife`, `topheap`, `sym2`, `swap`, `iswap`, `cswap`, `copycol`, `floatit2D`, `copyarr2D`, `copyiarr2D`, `plus2Dint`, `minus2Dint`, `plus2D`, `minus2D`, `total2D`, `total2Dint`, `lkodeitbb`, `ldekodeitbb`, `kodeitbb`, `dekodeitbb`, `expmod`, `nextprime`, `isprime`, `irevcomp`, `lrevcomp`, `ismatch`, `pmult`, `pdiff`, `mkfull`, `ivswap`, `vswap`, `setlong`, `lmod`, `printlmatx`, `printlmatwfile`, `floatitl`, `lvsp`, `lvvp`, `lvvm`, `exp1minus`, `vn2`, `vnorm`, `vin`, `numintmatch`, `findlastgt`, `findflastgt`, `findflastle`, `nips2bytes`, `splitlong`, `visfinite`, `squish`, `lcshift`, `rcshift`, `putbit`, `getbit`, `printmatws`, `printmats`, `log2weight`, `timeofday`, `initarray_3Ddouble`, `initarray_4Ddouble`, `initarray_5Ddouble`, `copyarr5D`, `free3D`, `free4D`, `free5D`, `printmatstr`, `printmatwstr`

No module/header is closed by the T04 tool review. Completing the remaining
contracts requires additional evidence; these limitations are not a clean pass.

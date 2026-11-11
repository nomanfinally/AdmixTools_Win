# T02 — qpfstats and its data/helper connections

Scope notice (11 November 2026): this is historical audit evidence.
Inherited-bug repairs described here are not the current porting baseline.
See [the project-wide restoration](PORT_ONLY_SCOPE_RESTORATION.md) for
active sources, retained Windows adaptations and new reference results.

Status: **passed with limitations**, following the explicitly requested
[corrections](T02_qpfstats.corrections.md) on 10 November 2026. Findings
F034–F035/F039–F041 are fixed; F042 is a further fixed duplicate-name diagnostic
defect. Current source hashes and validation are in the
[correction evidence](T02_qpfstats.corrections.evidence.json).

The remainder of this report preserves the **initial review at `ff2029d`**,
which was reviewed with open upstream defects. Its tables, counts, source hashes,
commands and descriptions of ineffective behavior are historical, superseded
where indicated by the correction report. Shared M/H items and downstream tools
retain their own audit status.
Reference: `67bc219174a109951a9434e0a383ec464fb140ee`, qpfstats `1101`;
Windows retains `qpfstats.exe`, version `1101.w`. Working base: `e99074c` plus
the uncommitted source hashes in [the evidence record](T02_qpfstats.evidence.json).
Raw inputs, binaries, stdout, stderr, exits, build logs, sanitizer traces and
exact diffs are retained locally in `validation-results/hard-check/T02/`.
No user dataset, reference installation, Git commit or remote was modified.

## Contract and reachable paths

Reviewed the complete qpfstats source, its differences from the pinned tree,
`README.qpfstats`, the link rule, and relevant shared implementations/callers.
The pristine Linux source check compares 115 source/header/Makefile files with
their Git objects at the exact reference commit. Repaired Linux and sanitizer
builds live in separate `/home/user/admixtools-t02-*` directories.

| Path | Actual execution and audit scope |
| --- | --- |
| CLI / parameters | `readcommands`, getopt, `openpars/dostrsub/writepars/closepars`; string/int/double parsing, aliases, includes, BOM/NUL/UTF-16, both output streams and native termination statuses |
| Population selection | `setgk/gkignore`, list loading/duplicate checks, `seteglist/loadindx`, population order/base population, inbreed lists, population counts and checked matrix/index dimensions |
| Genotypes | `getsnps/getindivs/getgenos`, mcio/admutils/geno/mapfile, packed and transposed packed mapping, EIGENSTRAT, ANCESTRYMAP, PED/BED and compressed variants |
| SNP selection | chromosome/exclusion/X filters, bad-SNP list, `setwt/rmsnps/loadsnpxx`, genetic/physical positions, block construction, complete versus all-SNP missingness |
| Estimation | `counthets/calchet/loadaa`, `dofstnumx`, scaling, explicit f2/f3/f4 enumeration and basis coefficients, `dofstats`, ordinary/size-weighted accumulation, jackknife, covariance and matrix operations in libnick |
| Serialization | high/standard precision `dumpfstatshr/dumpfstats`, header/effective blocks, exact generated fstats bytes, output errors, no-output-file behavior |
| Consumers | actual fstats reads by qpfmv (including mixed f2/f3/f4 and standard errors), qpAdm, qpWave, qpmix, qpfit and qpGraph; automatic sibling qpfstats launch from qpAdm, qpWave, qpfit and qpGraph |
| Windows runtime | native sibling process execution and CRT quoting, shared binary CRT I/O, gzip/zlib, native temporary separators, process manifest, UTF-8/long paths, PowerShell invocation/redirection/Tee-Object |

Direct link items: M01, M11–M14, M17–M20, M24, plus reachable libnick functions
in M02–M10 and their headers. qpgsubs is linked because of copied graph helpers;
qpfstats main does not load, fit or render a graph. The copied `doff3`, graph
mixture helpers and binary `dumpit/dumpf3` functions are unreachable from this
tool's CLI/parameters, so they are not additional qpfstats modes. qpmix's copied
`mkfstats` function likewise has no call in its main path. qpfmvmix remains
unbuildable upstream (T38); it cannot provide a runtime consumer comparison.

The active scientific defaults remain upstream: allsnps unset becomes NO;
inbreed unset follows allsnps; an inbreed list forces the default to NO and
marks its named populations individually; hires and scaling default YES;
sizeweight defaults NO; X is excluded; block size defaults to 0.05 Morgans.
The test fixture sets block size 0.005 and seed 77 explicitly. No scientific
loop, enumeration order, RNG implementation, optimization flag or precision
was changed in this audit.

All parsed keys were traced. `scale/doscale`, `allsnps/useallsnps`,
`poplistname/poplist` and `instem` are exercised. `lambdascale` overrides automatic
scaling when positive; scale NO still forces 1. `outpop` is a weighting setting,
not a request to change the first population in the basis. Naming a different
listed population remaps it to index zero and fails the zero-population check;
the behavior is recorded rather than inventing another base-population rule.

## Initial review builds and comparison rules

- Windows: x86-64 UCRT64 GCC 16.2.0, GSL 2.8, OpenBLAS 0.3.34, zlib 1.4.
  All 37 supported native targets rebuilt. Existing application `-O2` and
  libnick `-O3`, `-fno-fast-math`, `-ffp-contract=off`, 64-bit file offsets
  and 8 MiB main-thread stack retained. OpenBLAS reports no USE64BITINT;
  the port does not substitute an ILP64 interface.
- Linux: WSL Ubuntu x86-64, GCC 15.2.0, GSL 2.8, OpenBLAS 0.3.32 pthread
  package. Pristine binaries/source hashes and corrected build commands are
  recorded. qpfstats's actual Linux dependency closure is libc/libm: its
  reachable linear algebra comes from libnick, despite broader link flags.
- ASan + UBSan: isolated repaired Linux, debug symbols, frame pointers,
  non-PIE, abort/halt on sanitizer findings. Process-lifetime leak detection is
  disabled; invalid-access/UB checks are not a leak-free certification.
- `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`,
  `OPENBLAS_CORETYPE=NEHALEM`, `LC_ALL=C`; explicit seeds 77, 123 and
  -2147483648 expose the ignored-seed behavior. Shared RNG probes independently
  compare 800,000 outputs against pristine glibc/libnick.
- Scientific text is exact at printed precision; generated files are compared
  by SHA-256/bytes. No numerical tolerance. The large `-V` stream is retained
  and compared in full; it is not filtered to result lines.

Allowed metadata changes are the existing narrow runner rules: CRLF/LF,
binary basename/`.exe`, requested `.w`, CPU/memory values, mapping addresses,
generated PID/temp path names/separators and gzip command operand quotation.
No scientific lines, explicit seeds or arbitrary error messages are normalized
away. Native abort is retained as -6 on Linux versus 3221226505 on this Windows
CRT. Failed gzip inputs, BOM acceptance, directory errno wording and truncated
packed-input zero-errno wording retain their raw differences.

The full matrices are `windows-verified`, `linux-verified`, `asan-verified`.
`*-closure` reruns supersede affected cases after the scale and consumer fixes.
The earlier `*-final`/`*-fixed` runs supply the unchanged verbose case. Exact
case origins, counts, comparisons and artifact hashes are in the evidence JSON;
counts include preparation and CLI/error cases, not that many scientific models.

| Final recorded check | Observation |
| --- | --- |
| Composed Windows / repaired Linux / ASan+UBSan matrix | 122 / 120 / 120 cases; no unexpected exit or invalid-access/UB finding in the final selected cases |
| Shared repaired Linux/Windows | 118 cases, including 86 jointly successful cases with both streams exact; 88 case/file comparisons exact |
| All shared streams, including failures | 230 of 236 exact; six differences in five explicitly recorded cases: BOM, corrupt/truncated gzip, output directory and truncated packed input |
| Current 35-case cross-suite regression | 69 of 70 streams exact; qpGraph's corrected population-name diagnostic is the sole stream difference; all 18 generated files and binary round trip exact |
| Before the qpGraph diagnostic repair | All 70 regression streams and all 18 generated files exact against pristine Linux |
| Native platform probes | 800,000 RNG values exact; integer rounding/sort output exact; sparse size/seek/binary I/O/mapping above 4 GiB passes on both systems |
| Native invocation | Windows PowerShell 5.1 direct redirection and Tee-Object exit 0; generated fstats hash matches the direct runner |
| Known cleanup failure | qpGraph automatic helper retains four files on both systems; Windows `--verify` reports it rather than granting a pass |

## Initial review findings (retained defects subsequently corrected)

F034, F035, F039, F040 and F041 below describe their state at the initial review.
They are now fixed as recorded in the [correction report](T02_qpfstats.corrections.md);
F042 is recorded there as well.

| ID | Classification / evidence | Action and compatibility consequence |
| --- | --- | --- |
| F026 | Upstream, high: list heap overwrite. `many-pops` has 60 population names and 54 individuals; pristine ASan catches an 8-byte write past qpfstats's pointer array. | Size from list rows and use a shared capacity-checked loader for population/inbreed lists. Existing callers retain the unbounded API until independently audited; ordering/comments/duplicate wording are unchanged. Probe tests exact capacity and rejection before append. |
| F027 | Upstream, high: missing/empty population list reaches invalid indices; pristine ASan catches an out-of-bounds read with no poplist. A one-population model has no f-statistic basis. | Require the documented population list and at least two populations before analysis allocations. Two/three-population fixtures remain valid. No undocumented automatic population-selection semantics were introduced. |
| F028 | Upstream, high: `np*np*np*np` overflows signed int at 216 populations; ASan reports a calloc size overflow. The coefficient product exceeds int capacity already at 58 populations. This affects LP64 and LLP64. | Check quartic and exact f2/f3/f4-count × basis products with 64-bit arithmetic before allocation. Probe 57 accepted / 58 rejected without allocating huge matrices; also 216, INT_MAX, zero and negative counts. This is a representability guard, not a claim that a 57-population analysis fits available RAM. |
| F029 | Upstream, high: `lambda-large` (1e100) triggers a stack overwrite in `dumpfstatshr`'s unused 128-byte sprintf/atof round trip. Pristine ASan records a 209-byte write. | Remove only the unused conversion. Keep the original fprintf precision and values. Corrected Linux/Windows large finite output agrees exactly. |
| F030 | Upstream, high: infinite lambda exits 0 and writes 702 NaN statistic/covariance lines in the fixture. | Extend the existing NaN scale check to reject nonfinite scale. Existing `scaling bug!` error retained. Finite/automatic/scaling-disabled calculations are unchanged. This does not certify every extreme finite arithmetic input. |
| F031 | Upstream, high: POSIX genotype gzip command executes twice and accepts nonzero gunzip status. `gzip-truncated` produces a successful scientific output from an incomplete stream. | Execute once; reject every nonzero status and remove the failed decompression output. Successful scientific bytes stay identical. Native Windows already rejects this through zlib. Native zlib versus external gunzip diagnostics still differ. |
| F032 | Windows, low: getopt error wording differs from glibc for invalid/missing-argument cases. | Reuse the existing Windows `admix_getopt` service, guarded by `_WIN32`; options and exit behavior retained. Successful help/version streams agree after basename/suffix normalization. |
| F033 | Upstream, low: parameter handle never closed. | Close it after parameter echo, as already done for qpAdm. No change to parsed values or terminal text. |
| F034 | Upstream, high; **open**: `popsizelimit: 3` prints three samples per population but still analyzes the pre-limit 54-row index. Its fstats bytes equal the six-sample baseline. | Record the exact reproducer and incorrect effective behavior. Rebuilding the analysis index would change scientific output; it is not disguised as a Windows compatibility repair. Do not rely on qpfstats for subsampling. |
| F035 | Upstream, medium; **open**: parsed `seed` and `-s` never reach SRAND. The population-limit path consumes the implicit default RNG state regardless of supplied seed. | Preserve the existing sequence and record 77/123/high-bit equivalence. Do not advertise user-selected qpfstats seeds as effective. Parent qpAdm/qpWave fitting seeds are separate. |
| F036 | Upstream consumer qpmix, high: two-source cached analysis prints six yy doubles from a four-double allocation; ASan catches the read at qpmix.c's `zzyy` diagnostic. | Bound that diagnostic to MIN(6,d*d). Only out-of-bounds garbage disappears; coefficient, SE and p-value lines are unchanged. Corrected sanitizer/Windows/Linux consumer reruns agree. |
| F037 | Upstream consumer qpGraph, high: fstats population diagnostics use an uninitialized count `x`. | Use the population count returned by `fstats2popl`. The names now print deterministically between the existing `+++` lines. This deliberately changes broken diagnostic output; it is not normalized away in pristine comparisons. Graph/result data remain byte-identical. |
| F038 | Upstream consumer qpfit, medium: its existing early exit bypasses helper-fstats removal. | Remove its generated fstats on that exit when keeptmp is NO. Preserve explicit input files and keeptmp. Parent analysis semantics are not enabled or rewritten. |
| F039 | Upstream consumer qpfit, high; **open**: unconditional `exit(0)` after `all OK!` makes later fitting code unreachable. Also pristine qpfit does not compile here because its local addscaldiag declaration conflicts with the upstream header. | Cached/automatic reads are tested on repaired Linux/Windows, not claimed as pristine qpfit numerical fitting parity. The prototype repair predates T02. Carry to T20 for an explicit upstream behavior decision. |
| F040 | Upstream consumer qpGraph / helper ownership; **open**: automatic qpfstats leaves four files (`fsx`, `ppp`, `pops`, `fstpar`) on both systems. Older helper callers do not inherit qpAdm's exclusive-reservation/fatal-cleanup lifecycle. | Keep raw directory snapshots. T02 does not certify parent collision/failure cleanup. Carry the shared lifecycle work to T03/T08/T20/M01/M02; no user file is deleted to make this assertion pass. |
| F041 | Inherited interface quirks; retained: `-g/-o/-x` are accepted but unused; help mentions absent `-b` and says `-v` exits although it continues. `doanalysis`, `quartet`, `fstdmode`, `useweights`, `diag`, `minvar`, `nostatslim`, `f3log`, `root`, and `output` do not change this main computation. Duplicate individual IDs remain accepted; duplicate SNP/population names fail. Nonpositive/NaN block lengths retain their inherited SNP/chromosome grouping behavior. | Document the actual behavior; do not infer features or change defaults from parameter names. Legacy-key and duplicate-ID cases are compared explicitly. |

## Architecture and presentation assessment

The native port method is appropriate for this compatibility baseline: shared
Win32 services, ordinary standalone executables, native sibling execution without
a shell, explicit binary I/O, consistent 64-bit file offsets and platform guards.
The new list check is shared rather than another Windows-only parser. No launcher,
UI banner, progress display, logging layer, color or Windows statistical fork was
introduced. PowerShell 5.1 direct redirection and Tee-Object both exit 0 and retain
the same generated fstats bytes. Native generated temp separators are asserted.

The upstream executable itself has substantial maintenance debt: copied inactive
graph routines, many unused globals/locals, unbounded historical interfaces,
quartic tables and an all-statistics × basis matrix whose memory cost becomes
large well before every int limit. Extra-warning output is retained and reviewed;
this is not a warning-free architecture claim. Removing the copied code or
redesigning those matrices would enlarge upstream merges and belongs after the
compatibility baseline. No optimization or scientific redesign was performed.

## Initial review reproduction and closure limits

From PowerShell, using a new directory per run:

```powershell
.\build-windows.ps1 -Msys2Root C:\msys64
python tests/windows/audit_qpfstats.py --bin bin --output validation-results/T02-windows
python tests/windows/audit_qpfstats.py --verify validation-results/T02-windows
python tests/windows/audit_qpfstats.py --compare validation-results/T02-linux validation-results/T02-windows
```

Use the same runner on the pinned pristine build and an isolated repaired Linux
build. `--select` accepts a case-name regex. `--verify` deliberately reports the
known qpGraph helper temporary leak; do not interpret its nonzero result as a
clean pass or suppress it. Comparisons retain native exits and all errors.
Sanitizer builds use the same commands/flags described in T01, now also building
qpmix, qpfit and qpGraph for the consumer checks. Compile `qpfstats_probe.c`
against real libnick; Linux uses function/data sections and `--gc-sections`;
the Windows probe also links qpfstats's direct dependency objects.

Actual tested scope is synthetic fixtures and these toolchains. No real cohort
was supplied for this audit. macOS runtime, network/UNC paths, forced termination,
disk/power loss, exhaustive low-memory behavior and all finite parameter values
are untested. The sparse >4 GiB probe tests actual shared native size/seek/mapping
services, not an end-to-end multi-gigabyte qpfstats cohort. Long paths pass on this
machine's enabled policy, not every Windows configuration. Other consumers retain
their own complete mode/error audits. The open findings kept T02 unchecked at this initial review. The subsequent
[correction report](T02_qpfstats.corrections.md) records closure and current limits.

# Tool and module compatibility audit

Inventory snapshot: 10 November 2026. Upstream baseline:
`67bc219174a109951a9434e0a383ec464fb140ee`.
Snapshot base HEAD: `9bfd9ee`; the inventory captured the port worktree before
its subsequent commit `145a0ca`. The recorded hashes describe that snapshot.

This is the queue for a hard compatibility and bug check **one item at a time**.
Items start **pending**. Previous passing fixtures are evidence to extend,
not a completed hard audit. Review results and their limitations are linked below;
creating this inventory does not certify a tool/module.

Scope restored on **11 November 2026**: Windows porting and presentation only.
Inherited Linux bug corrections from T01-T05 are removed from active source
and binaries; T06 already followed that scope. Scientific functions, defaults,
parameter acceptance and runtime behavior use the pre-audit port and the
unmodified pinned Linux oracle. Windows-only helpers and presentation changes
remain. See the [current restoration report](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md).

The machine-readable counterpart is
[`tests/windows/audit_inventory.json`](tests/windows/audit_inventory.json).
It records every source/header path, snapshot hashes, direct native link inputs,
shared-module relationships, existing coverage and stable item IDs. Static
archive inputs do not establish that every archive function is called by a tool.
New items get new IDs; do not renumber the existing queue.

## Scope and counts

| Inventory group | Items |
| --- | ---: |
| Build/install/maintenance controls | 10 |
| Example scripts/workflows | 7 |
| Header/ABI/default/table contracts | 40 |
| Historical Makefile targets with missing source | 10 |
| Installed interpreter helpers, Python modules and script test harness | 28 |
| Native tool targets (37 built, 1 blocked) | 38 |
| Shared C modules linked directly or available through libnick | 28 |
| Additional C programs with main(), outside supported build | 5 |
| Additional C modules outside supported links | 7 |
| Validation runners/probes | 46 |

Total: **219 audit items**, covering **78 production C sources and 40 headers** plus scripts and build/test controls.
I10 and Q07–Q08 were appended during T01; original snapshot hashes remain historical.
Q09–Q10 were appended during T02; snapshot hashes remain historical.
Q11–Q13 were appended during T03 and its corrections; snapshot hashes remain historical.
Q14–Q22 were appended during T04; original snapshot hashes remain historical.
Q23 was appended during the requested T04 corrections.
Q24-Q29 were appended during T05; original snapshot hashes remain historical.
Q30 was appended during T05 corrections; original evidence is retained.
Q31-Q37 were appended during T06; original snapshot hashes remain historical.
Q38 was appended during T06 corrections; original evidence is retained.
Q39 was appended for port-only restoration; original snapshot hashes remain historical.
Q40-Q46 were appended during T07; original snapshot hashes remain historical.

Data files, parameter templates (including `parsimp.templ` and
`parsimp2.templ`), reference logs, manuals and generated binaries are fixtures or
artifacts, not extra executables. Review their use under the relevant tool.
`src/Makefile.mac` references a `pysrc/` directory absent in this checkout; track
that under I05 rather than inventing missing Python tools.

## Sequential queue

First: **T01: qpAdm**. It is the main user workflow and exercises parameter
parsing, packed/text input, temporary files, rank fitting and automatic qpfstats.
Then T02 qpfstats, T03 qpWave, and the remaining T rows in numerical order.
Examine their shared dependencies while checking each tool; close a module's own
M/H item only when its applicable contract checks are complete. A tool pass does
not automatically close all modules it links.

After T items, close any remaining M/H items, then S, E, L/U/R scope decisions,
and I/Q controls. Blocking defects may require checking a dependency or I item
sooner; record that dependency and resume the current tool afterward. T38 is
blocked pending an established upstream algorithm/reference, not permission to
guess the intended statistical expressions.

Current compatibility baseline: **port-only restoration**, with rebuilt native
binaries and new pinned-pristine comparisons. Earlier T01-T06 reviews remain
historical evidence, not current hard-audit passes. Independent coverage and
shared-module reviews remain open; full-suite parity is not certified.

The [restoration report](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md) records removed upstream corrections,
retained Windows adapters/presentation, source and binary hashes, comparison
results and remaining limitations. Resume the applicable coverage reviews against
this restored baseline; do not use repaired-Linux expectations as the oracle.
The [12 November T04 recheck](tests/windows/audits/T04_PORT_ONLY_SCOPE_RECHECK_20261112.evidence.json)
confirms restored qpDstat behavior against pristine Linux in ten focused cases;
the inherited Linux defects remain deferred.

## Native executable queue

`Default` means an upstream default/install target; `Additional` means another
supported upstream Makefile target. All supported binaries live under `bin/`.
`Fixture` means previous selected numerical/output fixtures passed; `Build only`
means no dedicated scientific fixture yet. A completed review must link its report
and state its limits; it does not close related modules automatically.

| Done | ID | Tool | Role | Target | Previous evidence |
| --- | --- | --- | --- | --- | --- |
| [ ] | T01 | `qpAdm` | Admixture model fitting | Default | [Restored; coverage pending](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md) |
| [ ] | T02 | `qpfstats` | F-statistic precomputation and helper process | Default | [Restored; coverage pending](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md) |
| [ ] | T03 | `qpWave` | Rank/ancestry-stream tests | Default | [Restored; coverage pending](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md) |
| [ ] | T04 | `qpDstat` | D/f4 statistics | Default | [Restored; coverage pending](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md) |
| [ ] | T05 | `qp3Pop` | Three-population statistics | Default | [Restored; coverage pending](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md) |
| [ ] | T06 | `qpF4ratio` | F4-ratio estimation | Default | [Restored; Linux bugs deferred](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md) |
| [ ] | T07 | `qp4diff` | Differences between four-population statistics | Default | [Reviewed; open compatibility gaps](tests/windows/audits/T07_qp4diff.md) |
| [ ] | T08 | `qpGraph` | Admixture graph fitting | Default | Fixture |
| [ ] | T09 | `qpreroot` | Graph rerooting, scripts and optional rendering | Default | Fixture |
| [ ] | T10 | `convertf` | Genotype format conversion | Default | Fixture |
| [ ] | T11 | `transpose` | Packed genotype transpose | Default | Fixture |
| [ ] | T12 | `geno_single` | Single-individual packed extraction | Default | Fixture |
| [ ] | T13 | `merge_transpose` | Transposed genotype merge | Default | Fixture |
| [ ] | T14 | `mergeit` | Two-dataset genotype merge | Default | Fixture |
| [ ] | T15 | `snpunion` | SNP union/intersection workflow | Default | Build only |
| [ ] | T16 | `multimerge` | Multiple-dataset merge | Default | Build only |
| [ ] | T17 | `qpff3base` | F3-basis statistics | Default | Fixture |
| [ ] | T18 | `qpfmv` | F-statistic mean/variance utility | Default | Fixture |
| [ ] | T19 | `qpmix` | Mixture fitting | Default | Build only |
| [ ] | T20 | `qpfit` | Legacy rank/admixture fitting | Additional | Build only |
| [ ] | T21 | `qpBound` | F-statistic bounds | Default | Build only |
| [ ] | T22 | `qpDpart` | Partitioned D-statistic implementation | Default | Build only |
| [ ] | T23 | `qpdslow` | Alternative D-statistic implementation | Additional | Build only |
| [ ] | T24 | `rolloff` | LD-decay dating | Additional | Fixture |
| [ ] | T25 | `rolloffp` | Alternative rolloff implementation | Additional | Fixture |
| [ ] | T26 | `mkweights` | SNP-weight generation | Additional | Build only |
| [ ] | T27 | `kimf` | Graph/spectrum fitting | Additional | Build only |
| [ ] | T28 | `gcount` | Allele-count/site-pattern spectra | Additional | Build only |
| [ ] | T29 | `ascore` | Ancestry-score utility; characterize upstream behavior | Additional | Build only |
| [ ] | T30 | `easystats` | Dataset summary statistics | Default | Fixture |
| [ ] | T31 | `easylite` | Lightweight dataset statistics | Default | Fixture |
| [ ] | T32 | `easycheck` | Dataset integrity/duplicate checks | Default | Fixture |
| [ ] | T33 | `nickhash` | Individual/SNP name hashing | Default | Fixture |
| [ ] | T34 | `grabpars` | Parameter extraction | Default | Fixture |
| [ ] | T35 | `simpjack2` | Jackknife summary utility | Default | Fixture |
| [ ] | T36 | `dowtjack` | Weighted jackknife summary utility | Default | Fixture |
| [ ] | T37 | `diffmean` | Paired summary comparison | Additional | Fixture |
| [ ] | T38 | `qpfmvmix` | Blocked f-statistic mixture utility | Additional | Blocked upstream |

T38 `qpfmvmix` contains undefined `q`, incomplete `pops[ab ;`, and a malformed
link dependency. Separate upstream algorithm repair from Windows adaptation.
Its source stays in the audit inventory even though no executable is produced.

## Shared C modules

These are all 28 non-main C sources used in native direct links or the nick
archive. Windows-only services are included. A module check must cover boundary
values, ownership/lifetimes, error paths, integer width/ABI, numerical order and
its callers; a source read alone is insufficient.

| Done | ID | Module | Focus |
| --- | --- | --- | --- |
| [ ] | M01 | `src/win32/compat.c` | Win32 I/O, environment, PRNG, temp paths, gzip and process helpers |
| [ ] | M02 | `src/nicksrc/strsubs.c` | Strings, files, temporary names, errors and legacy shell helpers |
| [ ] | M03 | `src/nicksrc/getpars.c` | Parameter parsing/substitution and Windows quoting |
| [ ] | M04 | `src/nicksrc/gauss.c` | Gaussian sampling and random-dependent routines |
| [ ] | M05 | `src/nicksrc/gds.c` | General distribution/sampling helpers |
| [ ] | M06 | `src/nicksrc/sortit.c` | Sorting and equal-key ordering |
| [ ] | M07 | `src/nicksrc/xsearch.c` | Hashes, search tables and integer shifts |
| [ ] | M08 | `src/nicksrc/vsubs.c` | Vector/integer operations, rounding, memory/timing diagnostics |
| [ ] | M09 | `src/nicksrc/statsubs.c` | Statistical distributions, tails and jackknife routines |
| [ ] | M10 | `src/nicksrc/linsubs.c` | Linear algebra helpers |
| [ ] | M11 | `src/mcio.c` | Genotype formats, filters, sizes, gzip dispatch and readers/writers |
| [ ] | M12 | `src/geno.c` | Packed genotype matrices and byte operations |
| [ ] | M13 | `src/mapfile.c` | Memory-mapped file lifecycle and offsets |
| [ ] | M14 | `src/admutils.c` | Population/SNP/individual records and genotype access |
| [ ] | M15 | `src/h2d.c` | Diploid/haploid conversion helpers |
| [ ] | M16 | `src/exclude.c` | Exclusion/filter support |
| [ ] | M17 | `src/qpsubs.c` | Shared population/f-statistic computations |
| [ ] | M18 | `src/egsubs.c` | Population and genotype analysis helpers |
| [ ] | M19 | `src/ldsubs.c` | LD/block calculations |
| [ ] | M20 | `src/regsubs.c` | Regression helpers |
| [ ] | M21 | `src/f4rank.c` | Rank fitting and covariance operations |
| [ ] | M22 | `src/eigsubs.c` | Eigenvalue/eigenvector helpers |
| [ ] | M23 | `src/eigx.c` | LAPACK/BLAS declarations and ABI |
| [ ] | M24 | `src/qpgsubs.c` | Graph representation, traversal, serialization and DOT output |
| [ ] | M25 | `src/gslqp.c` | Graph optimization bridge |
| [ ] | M26 | `src/gslrank1.c` | Rank-one optimization bridge |
| [ ] | M27 | `src/qpfitr1.c` | Rank-one fit helper |
| [ ] | M28 | `src/gslkim.c` | Spectrum/graph optimization bridge |

## Headers, ABI, defaults and tables

Each header has its own contract item so declarations, signed widths, format
macros, global initializers, lookup tables and inactive platform branches are
not lost between C-module checks. Pair each header with its users.

| Done | ID | Header |
| --- | --- | --- |
| [ ] | H01 | `src/admutils.h` |
| [ ] | H02 | `src/badpairs.h` |
| [ ] | H03 | `src/egsubs.h` |
| [ ] | H04 | `src/eigsubs.h` |
| [ ] | H05 | `src/exclude.h` |
| [ ] | H06 | `src/f4rank.h` |
| [ ] | H07 | `src/faidx.h` |
| [ ] | H08 | `src/fitsubs.h` |
| [ ] | H09 | `src/geno.h` |
| [ ] | H10 | `src/globals.h` |
| [ ] | H11 | `src/h2d.h` |
| [ ] | H12 | `src/ldsubs.h` |
| [ ] | H13 | `src/mapfile.h` |
| [ ] | H14 | `src/mcio.h` |
| [ ] | H15 | `src/mcmcpars.h` |
| [ ] | H16 | `src/nicklib.h` |
| [ ] | H17 | `src/nicksam.h` |
| [ ] | H18 | `src/nicksrc/admix_platform.h` |
| [ ] | H19 | `src/nicksrc/admix_types.h` |
| [ ] | H20 | `src/nicksrc/getpars.h` |
| [ ] | H21 | `src/nicksrc/linsubs.h` |
| [ ] | H22 | `src/nicksrc/mptable.h` |
| [ ] | H23 | `src/nicksrc/nicklib.h` |
| [ ] | H24 | `src/nicksrc/ranmath.h` |
| [ ] | H25 | `src/nicksrc/sortit.h` |
| [ ] | H26 | `src/nicksrc/statsubs.h` |
| [ ] | H27 | `src/nicksrc/strsubs.h` |
| [ ] | H28 | `src/nicksrc/twtable.h` |
| [ ] | H29 | `src/nicksrc/vsubs.h` |
| [ ] | H30 | `src/nicksrc/xsearch.h` |
| [ ] | H31 | `src/packit.h` |
| [ ] | H32 | `src/qpgsubs.h` |
| [ ] | H33 | `src/qpsubs.h` |
| [ ] | H34 | `src/qsubs.h` |
| [ ] | H35 | `src/regsubs.h` |
| [ ] | H36 | `src/tmcio.h` |
| [ ] | H37 | `src/win32/argp.h` |
| [ ] | H38 | `src/win32/compat.h` |
| [ ] | H39 | `src/win32/mman.h` |
| [ ] | H40 | `src/xpsubs.h` |

## Installed scripts and Python modules

These are source locations, not just distinct basenames. Duplicate `fxtract`
and `xtractcol` files must be checked separately. Interpreter dependencies and
shell pipelines are part of compatibility. Installation does not establish that
a script runs on Windows. The Python test harness is currently copied by
upstream's directory-wide install and therefore remains visible here.

| Done | ID | Source | Installed destination | Previous evidence |
| --- | --- | --- | --- | --- |
| [ ] | S01 | `perlsrc/dof4` | `bin/dof4` | no dedicated parity fixture recorded |
| [ ] | S02 | `perlsrc/dof4a` | `bin/dof4a` | no dedicated parity fixture recorded |
| [ ] | S03 | `perlsrc/fxtract` | `bin/fxtract` | no dedicated parity fixture recorded |
| [ ] | S04 | `perlsrc/getresult` | `bin/getresult` | no dedicated parity fixture recorded |
| [ ] | S05 | `perlsrc/jackdiff` | `bin/jackdiff` | no dedicated parity fixture recorded |
| [ ] | S06 | `perlsrc/mkpretty` | `bin/mkpretty` | no dedicated parity fixture recorded |
| [ ] | S07 | `perlsrc/numlines` | `bin/numlines` | no dedicated parity fixture recorded |
| [ ] | S08 | `perlsrc/xtractcol` | `bin/xtractcol` | no dedicated parity fixture recorded |
| [ ] | S09 | `perlsrc/xtractcoltab` | `bin/xtractcoltab` | no dedicated parity fixture recorded |
| [ ] | S10 | `perlsrc/xtractcolv` | `bin/xtractcolv` | no dedicated parity fixture recorded |
| [ ] | S11 | `perlsrc/xtractcolx` | `bin/xtractcolx` | no dedicated parity fixture recorded |
| [ ] | S12 | `src/fxtract` | `bin/fxtract` | F001 install selection fixed; interpreter workflow audit pending |
| [ ] | S13 | `src/rexpfit.r` | `bin/rexpfit.r` | no dedicated parity fixture recorded |
| [ ] | S14 | `src/script/convertf.py` | `bin/script/convertf.py` | 12-file Python workflow; hard check pending |
| [ ] | S15 | `src/script/extract_individuals.py` | `bin/script/extract_individuals.py` | 12-file Python workflow; hard check pending |
| [ ] | S16 | `src/script/geno_header.py` | `bin/script/geno_header.py` | 12-file Python workflow; hard check pending |
| [ ] | S17 | `src/script/grepcol` | `bin/script/grepcol` | no dedicated parity fixture recorded |
| [ ] | S18 | `src/script/grepcolf` | `bin/script/grepcolf` | no dedicated parity fixture recorded |
| [ ] | S19 | `src/script/hash_checks.py` | `bin/script/hash_checks.py` | 12-file Python workflow; hard check pending |
| [ ] | S20 | `src/script/link_identical_files.py` | `bin/script/link_identical_files.py` | no dedicated parity fixture recorded |
| [ ] | S21 | `src/script/merge_transpose.py` | `bin/script/merge_transpose.py` | 12-file Python workflow; hard check pending |
| [ ] | S22 | `src/script/mktmp` | `bin/script/mktmp` | no dedicated parity fixture recorded |
| [ ] | S23 | `src/script/nick_hash_file.py` | `bin/script/nick_hash_file.py` | 12-file Python workflow; hard check pending |
| [ ] | S24 | `src/script/platform_compat.py` | `bin/script/platform_compat.py` | 12-file Python workflow; hard check pending |
| [ ] | S25 | `src/script/read_group_categories.py` | `bin/script/read_group_categories.py` | no dedicated parity fixture recorded |
| [ ] | S26 | `src/script/test_hash_merge.py` | `bin/script/test_hash_merge.py` | no dedicated parity fixture recorded |
| [ ] | S27 | `src/script/xtractcol` | `bin/script/xtractcol` | no dedicated parity fixture recorded |
| [ ] | S28 | `src/wtjack.pl` | `bin/wtjack.pl` | no dedicated parity fixture recorded |

## Additional source-only programs

These have a main() entry point but no supported installed target. Characterize provenance, intended invocation, dependencies and buildability before deciding supported scope. No parity or build success is implied.

| Done | ID | Item | Source / details |
| --- | --- | --- | --- |
| [ ] | L01 | `src/kimqpr.c` | `src/kimqpr.c` |
| [ ] | L02 | `src/testr1.c` | `src/testr1.c` |
| [ ] | L03 | `src/nicksrc/esttime2.c` | `src/nicksrc/esttime2.c` |
| [ ] | L04 | `src/nicksrc/kimf.c` | `src/nicksrc/kimf.c` |
| [ ] | L05 | `src/nicksrc/linsolve.c` | `src/nicksrc/linsolve.c` |

## Additional unbuilt C modules

These sources are present but do not enter supported Windows links. Classify their callers/dependencies and intended status; do not silently delete or optimize them.

| Done | ID | Item | Source / details |
| --- | --- | --- | --- |
| [ ] | U01 | `empr` | `src/empr.c` |
| [ ] | U02 | `fourier` | `src/fourier.c` |
| [ ] | U03 | `fstats` | `src/fstats.c` |
| [ ] | U04 | `kimqpg` | `src/kimqpg.c` |
| [ ] | U05 | `gcd` | `src/nicksrc/gcd.c` |
| [ ] | U06 | `qpsubsarti` | `src/qpsubsarti.c` |
| [ ] | U07 | `xqpsubs` | `src/xqpsubs.c` |

## Historical rules with absent source

These names are present in Makefiles but cannot be counted as working programs. Restore a pinned source/reference or explicitly document them as historical.

| Done | ID | Item | Source / details |
| --- | --- | --- | --- |
| [ ] | R01 | `oldqpmix` | `src/Makefile`, `src/Makefile.mac`; missing `src/oldqpmix.c` |
| [ ] | R02 | `qpf4diff` | `src/Makefile`, `src/Makefile.mac`; missing `src/f4diff.c` |
| [ ] | R03 | `qptestr1` | `src/Makefile`, `src/Makefile.mac`; missing `src/qptestr1.c` |
| [ ] | R04 | `qqAdm` | `src/Makefile`, `src/Makefile.mac`; missing `src/qqAdm.c` |
| [ ] | R05 | `qqpAdm` | `src/Makefile`, `src/Makefile.mac`; missing `src/qqpAdm.c` |
| [ ] | R06 | `qqpGraph` | `src/Makefile`, `src/Makefile.mac`; missing `src/qqpGraph.c` |
| [ ] | R07 | `qqpfmv` | `src/Makefile`, `src/Makefile.mac`; missing `src/qqpfmv.c` |
| [ ] | R08 | `qqpfstats` | `src/Makefile`, `src/Makefile.mac`; missing `src/qqpfstats.c` |
| [ ] | R09 | `qqpmix` | `src/Makefile`, `src/Makefile.mac`; missing `src/qqpmix.c` |
| [ ] | R10 | `w2p` | `src/Makefile`, `src/Makefile.mac`; missing `src/w2p.c` |

## Example workflows

Audit interpreter paths, current-directory assumptions, external commands, generated filenames and required example data.

| Done | ID | Item | Source / details |
| --- | --- | --- | --- |
| [ ] | E01 | `example.perl` | `convertf/example.perl` |
| [ ] | E02 | `ind2pheno.perl` | `convertf/ind2pheno.perl` |
| [ ] | E03 | `mklog` | `examples/mklog` |
| [ ] | E04 | `runit` | `examples.qpGraph/runit` |
| [ ] | E05 | `runqpgf` | `examples.qpGraph/runqpgf` |
| [ ] | E06 | `runqpgf2` | `examples.qpGraph/runqpgf2` |
| [ ] | E07 | `runqpreroot` | `examples.qpGraph/runqpreroot` |

## Build and maintenance controls

Audit reproducibility, archive/link ordering, platform guards, copied files/licenses, dependency closure, PATH handling and preservation of user data.

| Done | ID | Item | Source / details |
| --- | --- | --- | --- |
| [ ] | I01 | `Windows build entry point` | `build-windows.ps1` |
| [ ] | I02 | `GNU argp/dependency preparation` | `prepare-windows.ps1` |
| [ ] | I03 | `Windows target/link/install/manifest logic` | `src/build_windows.py` |
| [ ] | I04 | `Linux build/install rules` | `src/Makefile` |
| [ ] | I05 | `macOS build/install rules` | `src/Makefile.mac` |
| [ ] | I06 | `nick library build` | `src/nicksrc/Makefile` |
| [ ] | I07 | `C++ header-editing helper` | `src/add_extern_C.sh` |
| [ ] | I08 | `Historical exponential-fit shell template` | `src/expfit.templ` |
| [ ] | I09 | `Checkout, encoding and baseline policy` | `.gitattributes`, `.gitignore`, `UPSTREAM_BASELINE`, `AGENTS.md` |
| [ ] | I10 | `Windows application manifest` | `src/win32/admixtools.manifest`, `src/win32/admixtools.rc`; T01 path evidence, independent audit pending |

## Validation runners and probes

Audit the oracle and test runner too: expected failures, missing cases/files, timeouts, executable selection and metadata normalizations must not hide scientific differences.

| Done | ID | Item | Source / details |
| --- | --- | --- | --- |
| [ ] | Q01 | `parity.py` | `tests/windows/parity.py` |
| [ ] | Q02 | `compatibility.py` | `tests/windows/compatibility.py` |
| [ ] | Q03 | `script_helpers.py` | `tests/windows/script_helpers.py` |
| [ ] | Q04 | `platform_probe.c` | `tests/windows/platform_probe.c` |
| [ ] | Q05 | `largefile_probe.c` | `tests/windows/largefile_probe.c` |
| [ ] | Q06 | `stack_probe.c` | `tests/windows/stack_probe.c` |
| [ ] | Q07 | `audit_qpadm.py` | `tests/windows/audit_qpadm.py`; mode/error/format assertions and raw comparisons |
| [ ] | Q08 | `qpadm_probe.c` | `tests/windows/qpadm_probe.c`; shared hash, blocks, temporary ownership and output errors |
| [ ] | Q09 | `audit_qpfstats.py` | `tests/windows/audit_qpfstats.py`; direct modes, errors, formats and downstream consumers |
| [ ] | Q10 | `qpfstats_probe.c` | `tests/windows/qpfstats_probe.c`; real dimension/capacity boundaries without huge allocations |
| [ ] | Q11 | `audit_qpwave.py` | `tests/windows/audit_qpwave.py`; qpWave modes, exact comparisons, malformed inputs and physical-subset oracles |
| [ ] | Q12 | `qpwave_map_probe.c` | `tests/windows/qpwave_map_probe.c`; real failed-mapping propagation under a process-local Linux address-space limit |
| [ ] | Q13 | `qpwave_probe.c` | `tests/windows/qpwave_probe.c`; actual qpWave dimension guard at last-supported/first-overflowing boundaries |
| [ ] | Q14 | `audit_qpdstat.py` | `tests/windows/audit_qpdstat.py`; strict mode/input comparisons and independent allele/jackknife oracles |
| [ ] | Q15 | `audit_t04_modules.py` | `tests/windows/audit_t04_modules.py`; direct module probes and targeted sibling regressions |
| [ ] | Q16 | `build_t04_audit.py` | `tests/windows/build_t04_audit.py`; isolated Windows/pristine/port/sanitizer/coverage builds |
| [ ] | Q17 | `build_t04_probes.py` | `tests/windows/build_t04_probes.py`; production-function probe links |
| [ ] | Q18 | `inventory_t04_modules.py` | `tests/windows/inventory_t04_modules.py`; compiler-derived definitions, headers and warnings |
| [ ] | Q19 | `qpdstat_module_probe.c` | `tests/windows/qpdstat_module_probe.c`; bounded API/lifetime/dimension probes |
| [ ] | Q20 | `t04_argv_child.c` | `tests/windows/t04_argv_child.c`; native CRT argument-byte oracle |
| [ ] | Q21 | `t04_native_checks.ps1` | `tests/windows/t04_native_checks.ps1`; direct PowerShell/redirection/Tee/gzip path checks |
| [ ] | Q22 | `collect_t04_evidence.py` | `tests/windows/collect_t04_evidence.py`; retained-run summaries, sparse archive and independent module reports |
| [ ] | Q23 | `verify_t04_repairs.py` | `tests/windows/verify_t04_repairs.py`; repair verifiers, exact comparisons, source hashes and scoped closure evidence |
| [ ] | Q24 | `build_t05_audit.py` | `tests/windows/build_t05_audit.py`; isolated native/pristine/Linux/sanitizer/coverage builds |
| [ ] | Q25 | `audit_qp3pop.py` | `tests/windows/audit_qp3pop.py`; mode matrix, strict comparisons and independent allele/jackknife oracles |
| [ ] | Q26 | `build_t05_probe.py` | `tests/windows/build_t05_probe.py`; normal, coverage and explicit float-cast production-function probe links |
| [ ] | Q27 | `qp3pop_probe.c` | `tests/windows/qp3pop_probe.c`; sampling, lifetime, count, type-boundary and jackknife probes |
| [ ] | Q28 | `t05_native_checks.ps1` | `tests/windows/t05_native_checks.ps1`; native PowerShell invocation, paths, streams, Tee and gzip |
| [ ] | Q29 | `collect_t05_evidence.py` | `tests/windows/collect_t05_evidence.py`; source-checked evidence, supplemental probes and coverage collection |
| [ ] | Q30 | `verify_t05_repairs.py` | `tests/windows/verify_t05_repairs.py`; corrected matrices, original scientific comparisons, source/installed provenance and fault probes |
| [ ] | Q31 | `build_t06_audit.py` | `tests/windows/build_t06_audit.py`; isolated native/pristine/Linux/sanitizer/coverage builds |
| [ ] | Q32 | `audit_qpf4ratio.py` | `tests/windows/audit_qpf4ratio.py`; mode/input matrix, strict comparisons and independent f4-ratio/jackknife oracles |
| [ ] | Q33 | `build_t06_probe.py` | `tests/windows/build_t06_probe.py`; isolated production-function probe links |
| [ ] | Q34 | `qpf4ratio_probe.c` | `tests/windows/qpf4ratio_probe.c`; f4/count/ratio lifetime and boundary probes |
| [ ] | Q35 | `run_t06_probes.py` | `tests/windows/run_t06_probes.py`; Fraction oracle, native statuses and leak-detected lifetime checks |
| [ ] | Q36 | `t06_native_checks.ps1` | `tests/windows/t06_native_checks.ps1`; PowerShell/redirection/Tee/gzip/native-path checks |
| [ ] | Q37 | `collect_t06_evidence.py` | `tests/windows/collect_t06_evidence.py`; source-checked evidence, raw differences and fresh tool-only coverage |
| [ ] | Q38 | `verify_t06_corrections.py` | `tests/windows/verify_t06_corrections.py`; corrected matrices, independent oracles, original/pristine scientific differences, consumer and installed provenance |

Q39: [`port_only_scope.py`](tests/windows/port_only_scope.py), pristine-reference
builds and restoration cases; independent harness review pending.

T07 validation additions (independent harness checks remain pending):

| Done | ID | Runner/probe | Scope |
| --- | --- | --- | --- |
| [ ] | Q40 | `build_t07_audit.py` | Isolated Windows/pristine/Linux/sanitizer/coverage builds |
| [ ] | Q41 | `audit_qp4diff.py` | Both estimator modes, exact streams/statuses/data and eleven independent oracles |
| [ ] | Q42 | `build_t07_probe.py` | Current production-function and shared platform probe links |
| [ ] | Q43 | `qp4diff_probe.c` | Actual f4/count/block/workspace boundary and lifetime paths |
| [ ] | Q44 | `run_t07_probes.py` | Raw direct probe/LeakSanitizer results, RNG and >4 GiB platform checks |
| [ ] | Q45 | `t07_native_checks.ps1` | PowerShell/redirection/Tee/gzip/native and long-temp paths |
| [ ] | Q46 | `collect_t07_evidence.py` | Source/fixture/oracle invariants, explicit differences and hashed raw archive |

## Hard-check procedure for each item

1. **Freeze the evidence.** Record upstream commit, dirty-source hashes, actual
   executable hashes, compiler/link flags, dependencies/BLAS ABI, architecture,
   thread settings, locale, seeds and complete commands. Use the pristine pinned
   WSL reference, not an unknown binary on PATH. Preserve the user's installation.
2. **Read the contract and changes.** Inventory actual options, parameter keys,
   defaults, output files, helper calls and shared modules from source and
   upstream documentation. Compare Windows guards with original code. Do not
   assume every tool supports the same flags or formats.
3. **Exercise ordinary behavior.** Use small deterministic fixtures plus relevant
   real datasets. Compare scientific text at printed precision and generated
   data byte-for-byte. Compare stdout, stderr, ordering, help/version and exit
   status, with only individually recorded metadata exceptions.
4. **Exercise boundaries.** Cover zero/one/minimal records, missing/monomorphic
   data, duplicate populations/IDs, degenerate or ill-conditioned models,
   supported format conversions, integer/count/offset limits and accepted seed
   values. Apply only cases meaningful to that tool/module and justify N/A.
5. **Exercise failures and OS behavior.** Mutate parameters and file headers;
   test truncated files, wrong hashes, unknown options, missing inputs/helpers,
   denied output, existing temp/output files, interrupted operations and cleanup.
   Check CRLF/BOM/encoding, relative paths, spaces/metacharacters, Unicode/long
   paths, drive separators, native printed paths, pipes and redirection.
   Use isolated fixtures; never fill the user's disk or mutate original datasets.
6. **Inspect memory and undefined behavior.** Use supported warnings, sanitizers
   and diagnostic tools on isolated builds, especially in WSL. Investigate
   bounds, overflow, shifts, casts, uninitialized values, ownership, mappings,
   handles and subprocess status. A sanitizer finding in Linux is still a bug,
   not a Windows-only regression or permission to change statistical behavior.
7. **Classify every divergence.** Distinguish a Windows regression, existing
   upstream defect, dependency/platform difference, unsupported feature and
   harness defect. Keep raw failing input/output and a minimal reproducer.
   Fix additional Windows deviations. If the same defect occurs in pristine
   Linux, record and defer it; preserving that behavior is the current scope.
   Agreement with a separately repaired Linux build cannot close a pristine
   compatibility difference.
8. **Fix, regress and close.** Make the smallest guarded compatibility fix;
   preserve calculations, RNG order, defaults and terminal formatting. No new
   optimizations or inherited Linux bug repairs. Re-run the reproducer, affected
   callers and relevant existing
   parity cases. Attach the report before changing status. Residual gaps must be
   explicit; blockers/waivers are not a clean pass. Commit/push only if requested.

Use [`tests/windows/AUDIT_TEMPLATE.md`](tests/windows/AUDIT_TEMPLATE.md) for each
report. Put reports under `tests/windows/audits/` as work begins, and large/raw
artifacts under ignored `validation-results/hard-check/<ID>/`. Only mark an item
passed when the report's applicable checks and regression comparisons pass.
Keep a completed-with-open-limitations state distinct from a clean pass.

## Current finding disposition

T07 was reviewed on **12 November 2026** against pristine upstream. Its
[report](tests/windows/audits/T07_qp4diff.md),
[evidence](tests/windows/audits/T07_qp4diff.evidence.json) and
[connected-module review](tests/windows/audits/T07_connected_modules.md) record
69 jointly successful finite-result cases / 122 rows exact, eleven independent
oracles, native PowerShell and direct RNG/large-offset checks. The Windows
getopt diagnostic occurrence F044 is corrected in source and an isolated build.
**F088** remains an open gzip error/exit compatibility gap; **F089** records
Windows `nan` versus Linux `-nan` on undefined Z. **F090** is an inherited
low-block workspace leak. Existing inherited defects remain deferred, and all
module/header checks stay independently pending. T07 is not a clean pass and
the installed binary has not been replaced.

Windows installation order (F001), native quoted/Unicode paths and manifest,
owned Windows temporary handles, native helper execution and getopt/gzip
presentation remain. Help text may describe inherited behavior accurately.
Scientific, shared parser/validation, sampling/seed, X-counting, memory-safety,
output-checking and runtime/option changes that corrected inherited Linux bugs
are **deferred and removed from the active port**. The shared helper is now
Windows-only; Unix retains its previous implementation.

### Historical findings ledger

The states below describe archived audit/repair revisions, not the restored
source. Their corrections are superseded by the disposition above and the
[restoration report](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md). IDs and original evidence remain intact.

| Finding | Item | State | Observation | Next action |
| --- | --- | --- | --- | --- |
| F001 | I03; installed fxtract variants | Fixed; installed bytes verified | Windows now follows upstream install order: copy `perlsrc` helpers before `src/fxtract`. Installed `bin/fxtract` matches `src/fxtract` byte-for-byte. | See [T01 follow-up](tests/windows/audits/T01_qpAdm.corrections.md); independent I03/S12 workflow audits remain pending. |
| F002–F023 | T01; helper and shared runtime paths | Fixed; T01 passed with limitations | Upstream bounds/UB, single-source results, output errors, gzip PLINK dispatch, and Windows paths/temporary ownership. Each stable ID and reproducer is in the [T01 report](tests/windows/audits/T01_qpAdm.md). | Retain recorded broken-upstream differences; continue T02 and independent M/H/T reviews. |
| F024–F025 | T01; M11 / inherited CLI | Fixed in requested follow-up | Portable EOF diagnostic; version-only exit; correct help; inactive output/rank keys fail explicitly rather than misleading users. | See [T01 follow-up](tests/windows/audits/T01_qpAdm.corrections.md) for intentional interface changes and regression evidence. |
| F026–F033 | T02; M02/M11/M17/H27 | Fixed; regression evidence recorded | Population-list overwrite, invalid/overflowing dimensions, writer stack overwrite, nonfinite scale, ignored POSIX gunzip failure, CLI wording and parameter handle. | Retain deliberate broken-upstream differences; see the [T02 report](tests/windows/audits/T02_qpfstats.md). |
| F034–F035 | T02 | Fixed upstream scientific defects | Seed the existing RNG and apply sampling before index/weight construction. | Limited outputs intentionally differ from pristine; physical-subset oracles and exact corrected Linux/Windows comparisons pass. See [corrections](tests/windows/audits/T02_qpfstats.corrections.md). |
| F036–F038 | T19/T08/T20, exercised through T02 | Fixed narrow consumer defects | qpmix diagnostic over-read, qpGraph uninitialized diagnostic count, qpfit normal helper-fstats leak. | Consumer reruns pass on repaired Linux/Windows and sanitizers; these are not full downstream audits. |
| F039–F041 | T20/T08/T02 and helper lifecycle | Fixed; downstream full audits remain pending | Restore qpfit's existing fitting path and guard its dimensions; share owned helper lifecycle; reject inactive qpfstats controls, duplicate IDs and invalid block lengths; correct help. | See [corrections](tests/windows/audits/T02_qpfstats.corrections.md). No pristine qpfit fitting parity claim. |
| F042 | M07/H30; duplicate-name callers | Fixed upstream diagnostic defect | `finddupalt` returned a sorted position instead of an input index, naming the wrong duplicate. | Regression `z,z,a` now identifies `z`; independent shared-module/header audits remain pending. |
| F043 | T01; Bayesian rejection sampling | Fixed in requested follow-up | A per-sample positive rejection limit fails explicitly instead of looping without a bound; sample-array multiplication is checked before allocation and diagnostic counting uses 64 bits. | See [T01 follow-up](tests/windows/audits/T01_qpAdm.corrections.md). No partial Bayesian estimate or changed accepted-draw calculation. |
| F044 | T03; M01 | Fixed Windows diagnostic regression | qpWave bypassed the shared getopt adapter; invalid options and missing arguments had different wording. | Guarded adapter call, native rebuild and regression matrix; see [T03](tests/windows/audits/T03_qpWave.md). |
| F045 | T03; M14 | Fixed upstream scientific controls | Apply seeded sampling before the analysis index; seeds 77/123 match physical-subset oracles. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F046 | T03; M17/M11; block callers | Fixed upstream memory safety | Validate complete block labels and table/count/padding bounds; qpAdm and qpWave reject malformed IDs. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F047 | T03; matrix/index contracts | Fixed upstream dimension overflow | Wide product/int/addressability checks run before allocation; actual boundary probes pass. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F048 | T03; input/OAS contracts | Fixed upstream invalid setting/boundary handling | Require finite positive block size, finite diagonal settings and nonzero model dimensions. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F049 | T03; M17; cached consumers | Fixed upstream scientific input integrity | Complete finite tokens and required mean/covariance presence are checked; malformed cached data cannot imply zero. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F050 | T03; M11/M14 | Fixed upstream duplicate-ID acceptance | Use existing ID validation before genotype loading; four genotype-format rejections pass. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F051 | T03; CLI/parameter contracts | Fixed upstream misleading interface/output | Reject inactive output/legacy controls without truncating files; version-only exits and help is truthful. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F052 | T03; rank metadata | Fixed upstream uninitialized value | Assign dofjack from effblocks; direct/cached/eigen output remains unchanged. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F053 | T03; M01/M11 | Fixed tested Windows gzip diagnostics | Header/EOF/CRC/length failure text matches corrected Linux in six cases; raw OS exit codes remain documented. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F054 | T03; M13; mapped callers | Fixed upstream mapping failure propagation | Close/reject failed maps before returning an object; real Linux and injected Windows/Linux failures pass. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md); independent modules remain pending. |
| F055 | T03; M17; fstats header parsing | Fixed upstream token-boundary read | Require a following token after basepop; malformed bare-base headers now fail explicitly. | See [T03 corrections](tests/windows/audits/T03_qpWave.corrections.md). |
| F024/F044/F045/F048/F050/F051, T04 occurrences | T04 and related M/H items | Corrected in reproduced T04 scopes | Transposed EOF/CLI diagnostics, seeded sampling, setting checks, duplicate IDs and truthful output/version controls. | [T04 corrections](tests/windows/audits/T04_qpDstat.corrections.md). |
| F056–F060 | T04; M17/M18 | Corrected inherited memory/scientific defects | Local tree indices, banker/list bounds, bounded Fourier lags and actual jackknife SD. | [T04 corrections and numerical oracles](tests/windows/audits/T04_qpDstat.corrections.md). |
| F061–F069 | M03/M06/M07/M12/M18/M20; affected callers | Corrected reproduced module defects | Checked matrix dimensions/header/I/O/lifetime, defined hash arithmetic, bounded singular diagnostics, list/median cleanup and CRLF macros. | [T04 corrections](tests/windows/audits/T04_qpDstat.corrections.md); independent module reports remain incomplete. |
| F070 | T22 qpDpart; targeted caller regression | Corrected borrowed-row ownership | patternscore retains its caller's colprobs row; multiple quartets pass ASan and native checks. | [T04 corrections](tests/windows/audits/T04_qpDstat.corrections.md); not a full T22 audit. |
| F071–F072 | M11/T04/M20 | Corrected reproduced lifecycle/haploid-tree defects | Owned Unix gzip cleanup and explicit rejection of undefined single-allele tree corrections. | [T04 corrections](tests/windows/audits/T04_qpDstat.corrections.md). |
| F073 | M03; numeric parameter callers | Corrected inherited partial numeric conversion | Reject malformed/out-of-range scalar/vector integer and real tokens; retain caller-specific finite-domain checks. | [T04 corrections](tests/windows/audits/T04_qpDstat.corrections.md); valid boundaries and targeted sibling consumers pass. |
| F044/F045/F048/F050/F051, T05 occurrences | T05; M01/M11/M14/M17 | Corrected in reproduced T05 scopes | Shared Windows getopt diagnostics, seeded sampling, finite/domain/trim guards, duplicate validation and truthful CLI/unsupported controls. | [T05 corrections](tests/windows/audits/T05_qp3Pop.corrections.md); original comparisons and scoped regressions retained. |
| F074-F078 | T05; M02/M17 and related callers | Corrected inherited lifetime/scientific/bounds/output defects | Unified low-data cleanup, representable pair counts, bounds before reads, checked parser status and one ordered details stream. | [T05 corrections](tests/windows/audits/T05_qp3Pop.corrections.md); independent large-count, physical-subset, details and sanitizer checks pass. |
| F079-F081 | T05; documentation/estimator/output | Corrected inherited contract defects | Explain outgroup/inbreed settings, reject undefined normalized denominators and check detail flush/close errors. | [T05 corrections](tests/windows/audits/T05_qp3Pop.corrections.md); zero denominator, native broken-pipe and Linux /dev/full tests pass. |
| F082 | T05; M11/M14/M17; X consumers | Corrected missing ploidy metadata initialization | Ordinary/PED readers set F diploid; M/U retain legacy haploid behavior. Independent female/mixed/weighted/male/unknown X and genotype-format oracles pass. | [T05 corrections](tests/windows/audits/T05_qp3Pop.corrections.md); eight seed/X scientific changes from broken original runs are explicitly recorded. |

F001 evidence before correction (historical):

```text
src/fxtract      SHA256 0aaece665dd08afa57ff57f158ec415b404bea3f74b5793e5546910c2baa1a16
perlsrc/fxtract  SHA256 b53dfad23fd7f426078b23b40c036bc5426c49a9b8095a7ee700a10cfb9cfeaf
bin/fxtract      SHA256 b53dfad23fd7f426078b23b40c036bc5426c49a9b8095a7ee700a10cfb9cfeaf
```

After correction, `bin/fxtract` and `src/fxtract` both have SHA256
`0aaece665dd08afa57ff57f158ec415b404bea3f74b5793e5546910c2baa1a16`.

Other known gaps from `WINDOWS_PORT_STATUS.md` (11 scientific-fixture gaps,
compressed-input behavior beyond T01's coverage, remaining Unicode/path cases,
interpreter pipelines and macOS validation) remain open inputs to this audit.
They have not been converted into passing checks by listing them here.

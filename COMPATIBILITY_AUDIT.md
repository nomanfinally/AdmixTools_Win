# Tool and module compatibility audit

Inventory snapshot: 10 November 2026. Upstream baseline:
`67bc219174a109951a9434e0a383ec464fb140ee`.
Snapshot base HEAD: `9bfd9ee`; the inventory captured the port worktree before
its subsequent commit `145a0ca`. The recorded hashes describe that snapshot.

This is the queue for a hard compatibility and bug check **one item at a time**.
All items start **pending**. Previous passing fixtures are evidence to extend,
not a completed hard audit. No tool/module has been certified by creating this list.

The machine-readable counterpart is
[`tests/windows/audit_inventory.json`](tests/windows/audit_inventory.json).
It records every source/header path, snapshot hashes, direct native link inputs,
shared-module relationships, existing coverage and stable item IDs. Static
archive inputs do not establish that every archive function is called by a tool.
New items get new IDs; do not renumber the existing queue.

## Scope and counts

| Inventory group | Items |
| --- | ---: |
| Build/install/maintenance controls | 9 |
| Example scripts/workflows | 7 |
| Header/ABI/default/table contracts | 40 |
| Historical Makefile targets with missing source | 10 |
| Installed interpreter helpers, Python modules and script test harness | 28 |
| Native tool targets (37 built, 1 blocked) | 38 |
| Shared C modules linked directly or available through libnick | 28 |
| Additional C programs with main(), outside supported build | 5 |
| Additional C modules outside supported links | 7 |
| Existing validation runners/probes | 6 |

Total: **178 audit items**, covering **78 C sources and 40 headers** plus scripts and build/test controls.

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

Current active hard audit: **none**. First queued: **T01**.
Completed hard audits: **0**.

## Native executable queue

`Default` means an upstream default/install target; `Additional` means another
supported upstream Makefile target. All supported binaries live under `bin/`.
`Fixture` means previous selected numerical/output fixtures passed; `Build only`
means no dedicated scientific fixture yet. Every checkbox remains unchecked.

| Done | ID | Tool | Role | Target | Previous evidence |
| --- | --- | --- | --- | --- | --- |
| [ ] | T01 | `qpAdm` | Admixture model fitting | Default | Fixture |
| [ ] | T02 | `qpfstats` | F-statistic precomputation and helper process | Default | Fixture |
| [ ] | T03 | `qpWave` | Rank/ancestry-stream tests | Default | Fixture |
| [ ] | T04 | `qpDstat` | D/f4 statistics | Default | Fixture |
| [ ] | T05 | `qp3Pop` | Three-population statistics | Default | Fixture |
| [ ] | T06 | `qpF4ratio` | F4-ratio estimation | Default | Fixture |
| [ ] | T07 | `qp4diff` | Differences between four-population statistics | Default | Fixture |
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
| [ ] | S12 | `src/fxtract` | `bin/fxtract (currently overwritten; F001)` | no dedicated parity fixture recorded |
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
   Do not pass a Windows bug merely because Linux also has a bug; explicitly
   track upstream defects and the compatibility consequences of any fix.
8. **Fix, regress and close.** Make the smallest guarded compatibility fix;
   preserve calculations, RNG order, defaults and terminal formatting. No new
   optimizations. Re-run the reproducer, affected callers and relevant existing
   parity cases. Attach the report before changing status. Residual gaps must be
   explicit; blockers/waivers are not a clean pass. Commit/push only if requested.

Use [`tests/windows/AUDIT_TEMPLATE.md`](tests/windows/AUDIT_TEMPLATE.md) for each
report. Put reports under `tests/windows/audits/` as work begins, and large/raw
artifacts under ignored `validation-results/hard-check/<ID>/`. Only mark an item
passed when the report's applicable checks and regression comparisons pass.
Keep a completed-with-open-limitations state distinct from a clean pass.

## Findings ledger

| Finding | Item | State | Observation | Next action |
| --- | --- | --- | --- | --- |
| F001 | I03; installed fxtract variants | Confirmed installation divergence; runtime impact not yet audited | Windows copies `src/fxtract` and then overwrites it with `perlsrc/fxtract`. Upstream `make install` copies in the opposite order, leaving `src/fxtract`. Current `bin/fxtract` matches the other source. | Fix and validate installation order during I03/script audit; retain both source variants in inventory. No fix made by this inventory change. |

F001 evidence from the current files:

```text
src/fxtract      SHA256 0aaece665dd08afa57ff57f158ec415b404bea3f74b5793e5546910c2baa1a16
perlsrc/fxtract  SHA256 b53dfad23fd7f426078b23b40c036bc5426c49a9b8095a7ee700a10cfb9cfeaf
bin/fxtract      SHA256 b53dfad23fd7f426078b23b40c036bc5426c49a9b8095a7ee700a10cfb9cfeaf
```

Other known gaps from `WINDOWS_PORT_STATUS.md` (11 scientific-fixture gaps,
compressed-input fatal cleanup/collisions, Unicode/long paths, remaining
interpreter pipelines and macOS validation) remain open inputs to this audit.
They have not been converted into passing checks by listing them here.

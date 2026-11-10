# T03 qpWave hard review

Historical initial review. The requested repairs are completed in
[T03 corrections](T03_qpWave.corrections.md), with current status **passed with
limitations**. The observations below preserve the pre-repair evidence.

Status: **reviewed with open defects; not passed**, 10 November 2026.
This is an audit of qpWave and the dependency paths its modes reach, not a
certification of those dependencies or the suite. No scientific algorithm,
statistical default, RNG, calculation order or result formatting was changed.
The only production change selects the existing Windows option-diagnostic
adapter. Open findings below require repairs and regression checks before T03
can pass.

Upstream: `67bc219174a109951a9434e0a383ec464fb140ee`. Work began at `9d764a2`
on a clean worktree; changes are uncommitted on `audit-t03-qpwave`.
The pristine Linux C sources/headers match that Git object byte-for-byte; the
reference tree was not patched. Linux port and sanitizer sources match the
starting worktree. After the guarded diagnostic repair, the non-Windows
preprocessed translation unit is **identical** to the previously tested Linux
port translation unit. Source/executable hashes, raw statuses, environments,
individual comparisons and artifact hashes are in
[the evidence record](T03_qpWave.evidence.json). Raw artifacts are under
`validation-results/hard-check/T03/` (ignored by Git).

For final reference provenance, pristine sources were copied into a fresh
isolated Linux tree and qpWave/qpfstats/convertf/transpose rebuilt with explicit
`-std=gnu11 -ffp-contract=off -fno-fast-math` and upstream optimization flags.
The exact compiler commands are retained in `build-pristine-strict.log` and
`build-pristine-strict.json`; the original reference tree remains untouched.

## Modes and connected code

| Path | Functions / modules reached | Scope |
| --- | --- | --- |
| Direct genotype analysis | `getsnps/getindivs/getgenos`, `gkignore`, `loadindx/loadsnpxx`, `setplimit`, `countpops`, `setblocksz`, local `doq4vecb/getf4`, `wjackvest` | M11-M14, M17-M20; text EIGENSTRAT, packed ancestry, transposed/mapped genotypes, ancestry records, PED/BED and gzip |
| Cached fstats | local `loadymv`, `fstats2popl/loadfstatsx/geteffblocks`, `setvv/vv2ww` | M17, M21 and input/header contracts; no genotype load or child |
| `allsnps: YES` | local `mkfstats` -> shared `qpfstats_helper` -> sibling `qpfstats` -> cached path | T02, M01-M03, M17; optional base population, explicit output/log, temporary directory and retention |
| Covariance and rank tests | `oascovar`, optional `eigvecs`, diagonal adjustment, `checkmv`, `f4info_init/doranktest/ranktest/printf4info` | M09-M10, M21-M23; OAS default, `oracle/oasmode`, `diagplus/diagvarplus`, eigenanalysis, verbose mode and rank boundaries |
| Command line and terminal | parameter parser, `printcmdline`, usage/version, `fatalx`, timing/memory | M01-M03, M08; `-p/-h/-v/-V`, streams, native PowerShell execution |

Direct link inputs are `qpWave.c`, `qpsubs.c`, `mcio.c`, `mapfile.c`,
`ldsubs.c`, `admutils.c`, `egsubs.c`, `regsubs.c`, `f4rank.c`, `eigsubs.c`,
`eigx.c`, `geno.c`, libnick, and Windows compatibility services. Relevant
headers include H01/H03/H04/H06/H09/H10/H13/H14/H16/H18-H21/H23-H30/H33/H35/H38/H39.
Archive membership is not a claim that every function executes.

`qpAdm`, `qpfit`, `qpGraph` and `qpfmv` are connected consumers of shared
statistics/helper or input code. They are not subprocesses launched by qpWave;
the only automatic executable is qpfstats. No Perl, Python or R interpreter is
required for qpWave's native analysis modes. The preparation matrix uses
`convertf` and `transpose` to generate native fixtures; that does not close
T10/T11. M/H items remain pending their own audits.

Version stays upstream `2201`, Windows `2201.w`. Default rank limit is clipped
to `min(nleft-1,nright-1)`; negative `maxrank` uses upstream's fallback of 4.
OAS defaults to YES and disables diagonal additions. Explicit cached input
skips genotype filtering. Automatic all-SNP mode delegates its filtering and
sampling to qpfstats. `oldallsnpsmode` is never read from the parameter file;
its direct legacy branch is unreachable through the supported CLI.
`numboot` is read but unused; `details` is not implemented for qpWave.
`hires` is not a qpWave rank-output mode. These are recorded interface facts,
not invented implementations. `-v` still continues, printing `no parameters`
to stderr when used alone, despite its help description; this inherited quirk
is not changed by F044.

## Validation and exact comparison

The final Windows matrix contains **132 cases**. The Linux port and ASan/UBSan
matrices each contain the same 132 cases using the full run plus the three
corrected cache fixtures; pristine Linux contains 130 (the two independent
physical-subset oracles are not pristine-tool cases). Preparatory conversions
and CLI checks are included in these totals. Separate native PowerShell/path,
large-file and mapping-failure probes are additional checks.

Against the Linux port, **82 jointly successful cases** have exact scientific
results and file bytes; **81** also match their complete normalized terminal
streams. The remaining case has different input parameter quotation and echoes
it as supplied (`forward-paths`, explained below). Joint success includes the
malformed inputs incorrectly accepted by both implementations; it is not a
count of 82 scientifically valid models or a safety pass.

An initial missing-covariance fixture removed a covariance irrelevant to the
selected f4s. Its replacement removes `cov(A,R1;A,R1)` and correctly fails on
both systems; it is not evidence of silent covariance acceptance. Missing mean
and invalid-number fixtures **do** change printed results with success (F049).
The initial block-file fixture used the wrong format; the final fixture uses
the actual `SNP_ID block_ID` contract. Earlier exploratory runs remain raw
history and are not substituted for the corrected cases.

| Check | Observation / artifacts |
| --- | --- |
| Ordinary calculations and printed results | Direct/cached/automatic, OAS on/off, diagonal additions, eigenanalysis, verbose, rank 0/1/saturated/negative fallback, square and minimal valid models; all successful shared scientific output matches the Linux port at printed precision. No numerical tolerance. |
| Scientific output bytes | Packed/transposed/PED/BED preparations and requested `saved.fstats` bytes compare exactly against the Linux port. Pristine gzip PED/BED failures are existing F021 repairs, not new regressions. |
| Pinned pristine comparison | Ordinary numerical outputs match. Limited automatic analyses intentionally differ because T02 fixed qpfstats sampling/seeding; retained temporary behavior and helper failures also contain previously documented repairs. These differences are retained in the diff. |
| Fixed-seed sampling | Six direct limit/seed variants still analyze 48 rows rather than 24. Two independently selected physical subsets give different results (F045). Automatic mode reflects the T02 qpfstats repair. |
| Missing data and chromosomes | Partial missing and all-missing data, monomorphic data, chromosomes 3/23, male X data, custom numchrom, map fallback and explicit physical map, bad-SNP list and explicit blocks exercised. Degenerate models fail; invalid block settings can succeed (F048). |
| Invalid inputs | Missing/empty/truncated files, malformed fstats/header/populations, duplicate lists/IDs, overlaps, UTF-16/NUL/BOM, corrupt/truncated/concatenated gzip, nonfinite settings; safe failures and remaining faults recorded individually. |
| Helpers and ownership | Sibling lookup, missing child/temp directory, child failure, copy failure, saved output/log, default cleanup, keep on success/failure. No owned-file leakage in the exercised current helper cases. Explicit user artifacts are retained. |
| Windows native operation | Windows PowerShell 5.1 redirection and Tee-Object exit 0; paths with spaces, `#`, UTF-8 accents; installation path with spaces/Unicode; long temporary path supplied with forward slashes. Printed generated paths use backslashes. Rank results unchanged. |
| LLP64, binary I/O and offsets | Existing >4-GiB sparse size/seek/read-map probe rerun successfully on Windows and Linux. Control bytes `0a 0d 1a ff` survive. `admix_long` preserves LP64 data offsets; BLAS/LAPACK integer declarations remain 32-bit. This is not an end-to-end >4-GiB qpWave scientific dataset. |
| Memory/UB | ASan/UBSan identifies block-table writes and signed dimension overflow (F046/F047). GCC warnings confirm the cached-mode uninitialized `dofjack` value (F052). A resource-limited real `constructMap` probe returns a live failed mapping (F054). No leak-free or memory-safe claim. |
| Platform source guards | Windows qpWave rebuilt using the normal build script. Warning builds on both systems succeed. The final non-Windows preprocessed source matches the tested Linux port exactly. macOS was not executed. |

Environment: x86-64 Windows UCRT64 GCC 16.2.0, GSL 2.8, OpenBLAS 0.3.34,
zlib 1.4; Linux GCC 15.2.0, GSL 2.8, OpenBLAS 0.3.32. `-O2` application code,
`-O3` libnick, `-ffp-contract=off -fno-fast-math`, no CPU-specific compilation,
32-bit BLAS integers, Windows 8-MiB stack. Linux ASan/UBSan uses non-PIE,
frame pointers and debug information. Existing reference/build metadata and
the fresh Windows build log are captured. Single-thread controls:
`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `OPENBLAS_CORETYPE=NEHALEM`,
`LC_ALL=C`; base parameter seed 77, variants 0/1/123/-2147483648. qpWave direct
mode ignores those seeds, which is an audited defect, not proof of seeded RNG
correctness. Leak detection is disabled; MSan/Windows ASan was not run.

Comparisons keep every scientific/result line. The reused normalizer substitutes
only: CRLF; executable installation paths and `.exe`; requested `.w` version
suffix; generated PID/temp paths and required Windows helper-path quotation;
mapping addresses; CPU times and memory values. Gzip command operand quoting is
normalized only for its generated temporary command. Original parameter values,
rank/chi-square/tail values, matrix rows and data bytes are retained.
The `forward-paths` fixture uses quoted Windows parameters and unquoted Linux
parameters: its parameter echo differs by construction; scientific results
match, and that stream difference is **not** suppressed.

Windows BOM/quoted-space-path support is an extension; those are not jointly
successful pristine comparisons. POSIX SIGABRT and Windows abort/access-violation
statuses differ, as do `return -1` process statuses (255 vs 4294967295).
Raw statuses are kept, including actual memory faults. Do not describe matching
nonzero/success categories as exact exit-status parity. Invalid gzip diagnostics
remain different (F053); they are not normalized away.

## Findings and proposed minimal repairs

| ID | Classification / severity / state | Reproducer, cause and consequence | Smallest next action |
| --- | --- | --- | --- |
| F044 | Windows output regression; low; **fixed** | `-z` and missing `-p` argument used MinGW's `unknown option -- z` and unquoted option character instead of Linux wording. qpWave bypassed `admix_getopt`, already used by qpAdm/qpfstats. | Guarded call to the existing adapter in `src/qpWave.c`. Normal options/help/version and direct/helper/rank fixtures rerun. The Windows abort status remains platform-specific. |
| F045 | Upstream scientific control defect; high; **open** | `popsizelimit: 3` reports `indivs: 48`; the physical-subset oracle has 24. `setplimit` runs after `loadindx` fixes the rows used by `countpops`; the declared seed is neither parsed nor initialized. Seed variants have identical direct rank results. Pristine reproduces. Automatic qpfstats sampling already works following T02, so modes now differ in whether the limit is effective. | Apply existing sampling before constructing analysis indices; explicitly define/parse/initialize the existing seeded RNG, retaining the no-random-operation default. Recheck both physical-subset seeds and all callers. This deliberately changes broken limited analyses and needs corrected Linux evidence. |
| F046 | Upstream shared memory safety; high; **open** | `blockfile-overflow`: 2,200 SNPs, each with block ID 2221. `setblocksz` allocates `numsnps+20`, then `setblocksf` writes `max_block+1` entries. ASan reports heap-buffer-overflow. ID 2147483647 also overflows `numbl+1`; pristine Linux and Windows crash. | Validate representability, label bounds and allocation/copy sizes before indexing; preserve valid block ordering/weights. M17/M11 and all `setblocksz` callers, including qpAdm, require recheck. |
| F047 | Upstream integer dimensions; high; **open** | `cached-dim-overflow`: 218 left and 218 right names with a small fstats file. `d=217*217=47089`; signed `dd=d*d` overflows before population membership is checked. UBSan reports the multiplication, ASan reports calloc overflow. Windows may reach a different error after UB. | Validate dimensions/products in a wide type before allocations and matrix APIs; reject impossible requests before fitting or reading cached matrices. Probe the real boundary without huge allocations. |
| F048 | Upstream invalid setting/boundary handling; medium; **open** | `blgsize: 0`, `-1`, or `nan` exits 0 with different block definitions; zero becomes 2,201 blocks. One-left input reaches zero-dimensional OAS and prints signed/unsigned NaN before failing. Pristine reproduces. Nonfinite diagonal settings fail later through linear algebra rather than validated input. | Require finite positive block size and valid nonzero analysis dimensions before shared numerical work; validate applicable covariance settings. Keep valid scientific defaults/output unchanged. |
| F049 | Upstream cached-data integrity; high; **open** | Delete the `A R1` mean row or replace its value with `invalid`. `loadfstatsx` leaves a zero-initialized cell or uses `atof`, accepting zero. Both exit 0; rank-0 chisq changes from 4.861 to 276.902. Pristine reproduces. Removing the relevant covariance instead fails in numerical code, so no silent-covariance claim is made. | Parse complete finite numeric tokens and track the required mean/covariance records; reject missing/malformed required data. Preserve valid printed fstats precision and population enumeration. Shared cached-data consumers require regressions. |
| F050 | Upstream input integrity; medium; **open** | `duplicate-ind` duplicates the first individual ID; direct text analysis exits 0. There is no `inddupcheck` after `getindivs`, unlike corrected qpfstats. This fixture retains the same populations/genotypes; it proves acceptance, not a demonstrated statistical difference. | Use the existing duplicate-ID validation before genotype loading; test ID-indexed ancestry and packed inputs as well as text. |
| F051 | Upstream interface/output defect; medium; **open** | `output:` and `outputname:` open/truncate the supplied file but never write results to it; stdout still contains all results and exit is 0. `-v` help also promises an exit that the code does not perform. `oldallsnpsmode`, `numboot`, and `details` have the inactive behavior described above. | Reject misleading inactive output controls or implement only a separately specified upstream-compatible contract; continue documenting shell redirection. Correct misleading help independently without adding banners or wrappers. Do not enable a new legacy scientific mode by guessing. |
| F052 | Upstream uninitialized metadata; medium/latent; **open** | `f4pt->dofjack = y` reads an uninitialized local in cached/automatic mode; eigenanalysis overwrites `y` in direct mode. GCC warns on Windows and Linux. `effblocks` already holds the right value. Current `printf4info/doranktest` do not consume `dofjack`, so no present printed numerical difference is claimed. ASan is not an uninitialized-read detector. | Assign `effblocks`, as qpAdm already does; verify rank output with/without cached input and eigenanalysis. |
| F053 | Windows terminal compatibility gap; medium; **open** | Corrupt/truncated gzip: Linux emits gzip's diagnostic plus shared error text; native zlib emits different error text/errno and lacks gzip's line. Both reject, but stderr is not identical. | Define and test a narrow compatible failure-diagnostic mapping, or explicitly document the exception before release. Retain raw differences; do not erase stderr to obtain a pass. |
| F054 | Upstream mapped-input failure handling; high; **open** | Real `constructMap` with a 4-GiB sparse file and address-space limit returns `genFile.snps == MAP_FAILED` after printing `error number: 12/n`. The probe regains control and exits 10. The caller can then dereference the failed mapping. The failure check is unchanged from pristine; this is separate from the successful >4-GiB API probe. | Fail immediately before constructing/returning the genotype object when mapping fails; preserve descriptors/ownership and test native Windows failure injection. M13 remains open. |

No scientific upstream repair above was silently folded into the port. The
production diff is four platform-guard lines; the helper, scientific loops,
precision, rank ordering, and version value are unchanged. F046/F049/F054 are
shared-code findings that also matter to other tools; prior limited T01/T02
evidence does not cover them automatically.

## Architecture, Windows presentation, and closure

The thin adaptation is appropriate: upstream source layout and individual
executables remain intact; the shared helper centralizes process execution,
safe parameter writing, owned temporary names and copying. Windows uses native
sibling execution and binary gzip I/O. The LAPACK ABI uses 32-bit integers
explicitly rather than replacing them with the port's 64-bit offset type.
There is no reason to restructure qpWave into a dispatcher, add UI decoration,
change numerical defaults, or introduce parallelism for this audit.

The useful improvements are precise input checks, truthful CLI/documentation,
bounded dimensions and shared error/ownership handling. Keep terminal
presentation upstream-compatible, including existing spelling/precision and
stdout/stderr routing. The Windows diagnostic repair reuses the shared adapter
instead of copying parser logic into another tool. Local `loadymv` duplicates
qpAdm/qpfit code; validation may eventually be shared once its full input
contract is tested, rather than refactoring the scientific transformations now.

Remaining limits: no macOS execution; no full-size research dataset or reference
incident reproduction; no end-to-end >4-GiB scientific run; no ILP64 BLAS,
32-bit Windows or alternate BLAS/compiler certification; no Windows sanitizer,
MSan, fault-injected Windows mmap failure, forced termination/power-loss cleanup
or complete resource-leak audit. Process-lifetime allocations and unreachable
cleanup in `oasrho` need the independent M/H reviews. The sparse probes verify
offset services, not every genotype-reader overflow boundary. Parent helper
checks are not a new full qpfstats/qpAdm/qpfit/qpGraph audit.

**Closure:** F044 is fixed and regression-tested. F045-F054 remain open.
T03 stays unpassed, the unresolved shared items retain their independent queue
status, and the next closure work is T03's defects rather than a clean-pass claim.

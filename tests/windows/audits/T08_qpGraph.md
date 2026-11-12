# T08 qpGraph

Status: **reviewed with open compatibility differences and deferred upstream
defects**, 12 November 2026. This is a hard-check report, not a clean pass or
full-suite parity certification. No scientific algorithm/default was repaired.

The oracle is pristine upstream `67bc219174a109951a9434e0a383ec464fb140ee`,
extracted from local Git objects; all **112 reference C/header hashes** match.
Working HEAD is `5c26fee` on the pre-existing `audit-t03-qpwave` branch. No
branch switch, commit, push, release or installed-binary replacement was made.

[Machine evidence](T08_qpGraph.evidence.json) contains every case status,
scientific score, generated-file/stream hash, build manifest, comparison
difference and direct/native result. [Connected modules](T08_connected_modules.md)
and the [compiler inventory](T08_modules.inventory.json) describe the reviewed
scope. Raw evidence and its hashed archive are under
`validation-results/hard-check/T08/`. Reproduction is in the
[test guide](../README.md#t08-qpgraph).

## Result

- The main matrix completed **101 native Windows cases** before the fixes,
  after the filename/getopt fixes, and after the helper fix. Pristine Linux,
  port Linux, sanitizer recovery and final Unix-source coverage each completed
  **100 cases**. Completion includes expected failures and timeouts.
- **56 jointly successful main fitting cases** have exactly the same printed
  scores. Two additional successful cases exercise an **interior admixture
  optimum** (0.621143 / 0.378857 in the saved mix file) and **two admixture
  nodes**, including the multi-mixture random-initialization path. Their entire
  normalized stdout and six scientific output artifacts match exactly.
- Every graph, DOT, f3 log, fitted-parameter dump, admixture file and outlier
  file actually produced by those jointly successful fitting cases matches
  pristine Linux byte-for-byte after CRLF/LF conversion alone. No numeric
  tolerance, result-line removal, NaN/sign normalization or reordered output
  establishes this result. Cases without requested output files are not counted
  as file comparisons.
- Full stream/status/file comparisons retain **64/101 exact** main
  pristine/Windows cases, **96/100** pristine/port Linux and **97/100** port
  Linux/coverage cases. Native abort status versus Unix signals, inherited UB,
  optional renderer diagnostics, helper-log metadata, quoted path/BOM extensions
  and the open Windows failures account for the other differences. They are
  listed individually, not silently converted to passes.
- Nine direct probe cases compare the actual constrained solver, graph paths,
  simplification, population deletion, 16 graph reload/free cycles, GSL bridge,
  rounding/tie sorting, **800,000 RNG values**, and sparse offsets/mapping
  beyond **4 GiB**. Ordinary native/pristine outputs match exactly. Independent
  small solver answers and graph-edge weight vectors also match. LeakSanitizer
  finds inherited leaks; these probes are not described as sanitizer-clean.
- PowerShell **5.1.26100.9818 / AMD64** checks direct execution, separate
  streams, Tee, Unicode working paths, helper temporary paths with spaces,
  native backslash display, text gzip, equal fitting scores and cleanup.
  Simplification leaves no `graphtt` base file or temporary file after the fix.
- Tool-local coverage: **30/44 functions, 976/1488 executable lines,
  430/826 branches taken**. `qpgsubs`: **55/110, 983/1957, 452/1078**.
  `gslqp`: **4/5, 71/77, 32/44**. Shared counters include fixture preparation,
  qpfstats and qpreroot calls; they are not qpGraph-exclusive reachability.

The authoritative native executable is
`validation-results/hard-check/T08/verified-build/snapshot/bin/qpGraph.exe`.
The installed `bin/qpGraph.exe`, `qpfstats.exe` and `qpreroot.exe` remain unchanged.

## Actual execution contract

`readcommands -> loadgraph -> explicit fstats OR native/shell qpfstats helper ->
fstats2popl/setbasep -> loadfstats -> basis/covariance construction -> constrained
edge solve/random initialization -> optional GSL simplex optimization -> fit,
outlier, graph, DOT, parameter and mixture output`.

| Surface | Source contract and checks |
| --- | --- |
| CLI | `-z/-p/-g/-s/-o/-d/-x/-l/-v/-V`; no arguments prints usage on stderr and exits 1. **`-h` is not parsed**, despite being advertised in inherited help. `-v` alone prints `7960[.w]`, stderr `no parameters`, and exits 0; with `-p` it continues analysis. Invalid/missing options, missing files, verbose and parameter-over-CLI precedence are tested. No new help option or exit behavior was added. |
| Data route | A successful run always obtains an fstats filename before fitting. Explicit fstats bypasses genotype reading. Otherwise qpfstats handles actual genotypes, filtering, missingness, blocks and binary mapping. The old direct-genotype fitting branches cannot ordinarily be selected merely by `oldallsnps` or `loadf3`; do not infer a second working estimator from their presence. |
| Graphs | New and legacy syntax; no admixture/tree, binary admixture, interior optimum, two admixtures, multiple ancestors, edge/admixture locks, zero legacy edge, rerooting, unknown roots/pops, changed base order, duplicate edge/target, cycles, missing/empty/short/long/bad-keyword graph cases. Three-way admixture is parsed but qpGraph fitting rejects nonbinary mixtures upstream. New-format extra `zero` is ignored; the legacy-zero case exercises an actual zero constraint. |
| Optimization | Fixed seed 77, 123 and -1; short `initmix` values 0/1/12; default GSL precision and .001; `optit: NO`, details and init/GSL verbose. The independent bridge uses a convex objective with known optimum .25/.75. Its convergence check is separate from strict cross-platform output comparison. No simplex method, penalty, evaluation order or RNG was changed. |
| Regularization | `diag`, `f2diag`, `minvar`, lambda scaling, sizeweight, bad-pair covariance, base-bad-pair rejection and inherited `lsqmode` obsolete message. The controlled successful fixture uses `diag: .0001`; an explicit `diag: 0` case reproduces the upstream singular-solver failure. This audit does not make regularization a new default or recommend changing a scientific model to force it to fit. |
| Modes | Analysis/no-analysis, no-analysis population list, quartet, full outlier, terse, fullvar, halfscore/halfjack, allsnps/inbreed/oldallsnps and ignored data controls with explicit fstats. Half-score is inherited-broken; its timeout/fatal evidence is retained. `phylipname` is parsed but its writer is inside the bypassed direct-genotype branch. |
| Persistence | Graph/DOT/f3/outlier/dump/mixture writes, reload via `loadname` and `admixin`, missing saved state, explicit helper log/fstats output and missing-parent destinations. `output:` truncates its file without writing results (F086); use stdout redirection. Dumped graph bytes are compared, not assumed to be a lossless inverse of every parser form. |
| Helper formats | Real EIGENSTRAT text, packed normal/transposed, valid gzip of all three; packed transpose round trips and prepared bytes are exact. Limiting, inbreed and allsnps delegated to qpfstats are exercised for compatibility. Broader PED/BED/ANCESTRYMAP, X/ploidy and giant real-cohort contracts remain with M11/T02 and are not newly certified by T08. |
| Failure/Windows paths | Missing genotype/helper output, failing child, failed optional copies, damaged gzip, missing/empty/short/NaN fstats, BOM/CRLF, quoted relative paths using either slash, Unicode and spaced working/temp paths. Windows path quoting and BOM support remain explicit extensions over pristine Linux. |
| Connected tools | qpfstats is an actual scientific child in automatic mode. qpreroot default/reroot/help and direct graph simplify/delete paths are tested. convertf/transpose prepare fixtures. qpGraph itself only writes DOT: it does not invoke Graphviz, Ghostscript, qpreroot or an interpreter. T09's broader scripts/renderers remain independently pending. |

## Findings

| ID / classification | Evidence and disposition |
| --- | --- |
| **F044 / Windows diagnostic regression, fixed** | qpGraph and connected qpreroot called raw MinGW getopt. Four guarded lines per caller select the existing adapter. `-h` remains an invalid qpGraph option, but now its error wording matches Linux. Valid CLI/scientific behavior is unchanged; version remains `7960.w`, Linux `7960`. |
| **F091 / Windows filesystem regression, fixed** | `gsimplify` wrote `graphtt:<pid>`, selecting an NTFS alternate data stream. The pre-fix direct probe succeeds but leaves an empty base file `graphtt`; fixed Windows uses `graphtt_<pid>` and leaves none. Direct simplify/delete outputs remain byte-identical to Linux. Unix retains its colon filename, directory and PID scheme. No graph traversal or serialization code changed. |
| **F092 / Windows helper-status regression, fixed in defined output paths** | Linux ignores qpfstats/cp status and then reads the selected fstats file. Windows previously aborted immediately. `auto-bad-log` now completes the same fit as Linux when only optional log copying fails. A fault-injection child copies valid fstats and exits **7**: original Windows aborts; final Windows and pristine Linux both finish with score **101.355**, exit 0 and the same child diagnostic. The change is conditional on `graphcall`; other helper callers retain their existing failure policy. Native copy errors remain stderr OS diagnostics. |
| **F088 / high / open shared Windows gzip compatibility gap** | CRC/truncated gzip: pristine qpfstats consumes decompressed data despite gunzip's nonzero child status, and qpGraph completes a fit. Native zlib rejects the input; no fit is produced. Changing only the parent cannot recover data rejected by the child. A shared M01/M11 repair needs focused cross-consumer evidence. This is a Windows deviation even though Linux's handling is an inherited defect. |
| **F093 / open Windows helper missing-output failure difference** | On missing genotype or a child that produces no fstats, upstream reaches an open/missing-file fatal. Windows reserves an empty fsx placeholder; after honoring upstream's ignored-child-status policy, that placeholder can reach the inherited empty-fstats null-base path, producing an access violation instead of an abort diagnostic. The case/status/empty intermediate file is retained. Distinguishing an untouched reservation from deliberately empty child output needs a focused lifecycle fix; treating all empty output as an upstream error would change the empty-file contract. |
| **F037 / inherited uninitialized diagnostic count, deferred** | Two `printstrings(fseglist, x)` calls use uninitialized local `x`. Earlier repaired-Linux evidence was not reused. Current successful optimized fixtures happen to print no such names; instrumented/platform runs are not guaranteed to do so. No initialization was added. |
| **F094 / inherited half-score undefined state, deferred** | Ordinary startup supplies fstats, bypassing the block-count initialization. `halfscore` then allocates/indexes with uninitialized `nblocks`; its secondary covariance is also not computed through the skipped direct-data branch. Pristine/port Linux cases time out or signal, native cases report matrix-not-positive-definite/abort. ASan is not an uninitialized-memory detector. This does not establish a valid half-score analysis on either OS. |
| **F095 / inherited graph/error input safety, deferred** | Duplicate-admixture `fatalx("node %s ...")` omits the argument; sanitizer reaches SEGV in vsprintf, and both ordinary platforms fail. Bad lock prints a pointer using `%d`, giving nondeterministic numbers. Empty fstats passes NULL into setbasep/strdup on both systems; short/bad graph handling has unchecked operands. MAXG/MAXPOPS and fixed line buffers also lack comprehensive capacity checks; enormous graph/population capacities were not exhaustively allocated. No Windows-only parser rejection was introduced. |
| **F096 / inherited ownership leaks, deferred** | Direct LeakSanitizer reports 48 bytes/3 allocations for the two constrained solves, 1619/8 for graph load/free, 3219/9 for simplify, 3251/10 for deletion, 49904/143 over 16 reloads, and 16/1 for the GSL bridge in this build. Stacks identify production allocations. Ordinary outputs still match pristine. Cleanup/refactoring is later upstream work; no scientific workspace order changed. |
| **F017/F048/F051/F086 / inherited shared/domain/interface behavior** | Hash signed shifts/overflow remain in qpfstats preparation. Nonfinite fstats are accepted and later fail the solver (`kode: -3` in the real NaN fixture). Partial scalar parsing, obsolete/inactive flags, negative/zero block inputs and output-file truncation are not repaired here. Previous sampling/X scientific corrections remain out of scope; matching this reference is not independent validation of those scientific defaults. |

One pre-existing port detail unnecessarily enlarged the **Unix** mkfstats stack
buffers and retained unreachable Windows branches inside its `#else`. This audit
restores that function verbatim to pinned upstream and keeps native Windows
helper code under its own guard. The collector proves all other qpGraph and
qpgsubs scientific source lines equal upstream after removing the enumerated
platform includes/types/version/getopt/helper/filename adapters.

## Architecture, provenance and limits

The direct per-executable port is appropriate for this compatibility stage:
upstream sources/layout, conditional version suffixes, one shared Windows helper
boundary, fixed-width LP64 arithmetic on LLP64, native binary I/O/zlib and a
native GSL bridge. No wrapper, dispatcher, algorithm optimization, default
change, tolerance widening or new dependency was introduced. Graph singleton
state, overlapping old/new readers, fixed capacities, recursion and workspace
ownership make maintenance harder; a broad redesign would complicate preserving
order and synchronizing upstream. Keep such work separate from compatibility.

Windows compiler: UCRT64 GCC **16.2.0**, x86_64-w64-mingw32/LLP64, GSL **2.8**,
available OpenBLAS **0.3.34**, zlib headers **1.4**, 8 MiB reserved main stack. Linux:
GCC **15.2.0**, x86-64/LP64, GSL **2.8**, OpenBLAS **0.3.32**, zlib **1.3.1**.
Both use upstream O2/O3, `-ffp-contract=off -fno-fast-math`, 32-bit BLAS integers,
one BLAS/OpenMP thread, NEHALEM core selection and C locale. Linux build commands
add `LDLIBS=-lnick` for upstream link order without modifying source. Native
qpGraph actually imports **GSL CBLAS** through `libgslcblas-0.dll`; despite the
`-lopenblas` link flag, OpenBLAS is absent from its DLL dependency closure.
Linux ldd includes OpenBLAS and GSL CBLAS. This dependency difference is explicit;
the successful numerical comparisons, not link-flag similarity, support parity.
Compiler,
flags, source/DLL/executable hashes and Linux ldd output are recorded.

Only generated temporary names/PIDs, address/CPU/memory metadata, requested
`.w`/`.exe` and newline conventions are normalized in stream comparisons.
Helper-log file comparisons deliberately retain their metadata/version
differences. Native abort codes and Unix signals are recorded literally.
Undefined lock diagnostics and half-score outputs are not normalized into parity.

During harness review, the original NaN substitution was found to match no
whitespace-padded fstats row. That original case is retained as a duplicate
ordinary fixture, **not NaN coverage**. Corrected `nan-*` matrices assert a real
input mutation and reproduce the upstream rejection. A native cleanup check
initially copied a pre-fix `graphtt` artifact into its work directory; the final
runner excludes that artifact and the separate before/after direct probe
demonstrates both its creation and removal. Neither harness error is counted as
a product fix or concealed as passing evidence.

No real cohort, exhaustive graph capacity, real >4 GiB genotype analysis,
native Windows sanitizer, macOS build, forced process termination, denied-ACL
matrix or renderer/PDF layout verification was completed. Independent M/H/Q
items and the broader T02/T09 audits remain open. The known shared gzip and
missing-output failure differences prevent T08 closure.

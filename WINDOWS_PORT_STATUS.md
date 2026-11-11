# Windows port status

The [11 November 2026 scope restoration](tests/windows/audits/PORT_ONLY_SCOPE_RESTORATION.md) removes inherited
Linux bug repairs from active sources/binaries. Windows porting and help
presentation are retained. Historical corrected-Linux audit results do not
certify this restored build; use the report's new pristine comparisons.

Development baseline: DReichLab/AdmixTools commit
`67bc219174a109951a9434e0a383ec464fb140ee` (upstream package 8.1.0).
Development is published on the
[`windows-port` branch](https://github.com/nomanfinally/AdmixTools_Win/tree/windows-port).
No release or MSI exists yet.

The complete tool/module inventory and sequential hard-check queue are maintained
in [COMPATIBILITY_AUDIT.md](COMPATIBILITY_AUDIT.md), with machine-readable sources
and dependencies in `tests/windows/audit_inventory.json`. No item is considered
hard-audited solely because the earlier fixtures passed.

## Scope

The Windows build produces 37 separate executables in upstream's `bin/` layout:
all 28 unique upstream default targets, plus 9 additional targets. Run
`python src/build_windows.py --list` for the authoritative inventory.
Runtime DLLs are copied beside the executables; MSYS2 is required for building,
but neither an MSYS shell, WSL, nor an MSYS runtime DLL is required to run them.
Interpreter-based helpers retain their upstream locations and still need their
respective interpreters.

`qpfmvmix` is explicitly blocked. Its upstream source contains `b=q` with an
undeclared `q` and the incomplete expression `pops[ab ;`; its link rule also
contains `eigx..`. There is no working Linux executable to compare at this
baseline. Repairing its intended statistical behavior requires a separate change.
Historical rules referring to absent sources (for example `qqpAdm`, `qptestr1`,
and `w2p`) do not constitute buildable upstream executables. Additional standalone
experimental sources in `nicksrc/`, `kimqpr.c`, and `testr1.c` are not installed by
the upstream Makefile and remain outside the supported build inventory.

## Compatibility changes

- Windows-only `.w` suffixes on existing version codes; `qpAdm` is `2206.w`.
- LP64-equivalent integer aliases and format strings on Windows LLP64, including
  genotype offsets, hash arithmetic, long-valued result arrays and rounding.
  Linux/macOS retain their original `long` types. LAPACK uses 32-bit integers.
- The default glibc-compatible random stream, binary CRT I/O, native file mapping,
  64-bit stat/seek, temporary directories, CPU time, and memory accounting.
- Equal-key sorting retains the input order observed in the Linux reference.
- Native sibling subprocess invocation for f-statistic precomputation and
  `kimf`'s `qpreroot` helper; in-process parameter filtering and file copying.
- GNU argp, pinned to commit `8ded2bc942740b5d291e450af661c5090dc3ca38`, with
  native executable basenames and one diagnostic quotation adjustment to match
  the Linux reference. Its LGPL notices must accompany future distributions.
- Windows quoted string parameters and CRLF merge lists accommodate native paths.
- Eleven illegal Windows filenames are renamed in place, preserving their bytes.
- An 8 MiB main-thread stack reserve matches the tested Linux reference's
  allowance, replacing MinGW's 2 MiB default without changing calculations.
- Native zlib gzip decompression, retaining the existing format readers and
  terminal labels; successful reads and decompression failures remove temporary
  files. No Unix gzip command is required. zlib's DLL/license are packaged.
- Native Graphviz/Ghostscript invocation for `qpreroot`'s optional PDF rendering.
- Python conversion/extraction/merge/hash helpers resolve native executables,
  quote Windows parameter paths, preserve LF data, and copy identical SNP bytes
  when Windows denies the upstream symlink operation for lack of privilege.

The local Sapphiregnm port was reviewed for compatibility techniques against
the pinned upstream source. See [WINDOWS_PORT_REVIEW.md](WINDOWS_PORT_REVIEW.md)
for the source inventory, decisions, and excluded behavior changes.

No new statistical defaults, data formats, SIMD, parallel execution, automatic
logging, combined executable, or optimization pass has been introduced.
Upstream's existing `-O2`/`-O3` levels are retained; contraction and fast-math are
disabled in the Windows build.

Upstream build defects were corrected without changing calculations:
the `libnick.a` link dependency for parallel default builds, missing `geno.o`
dependencies for `kimf`/`mkweights`, `diffmean`'s archive link order, and `qpfit`'s conflicting `addscaldiag`
declaration. Linux default builds were checked after the portability changes.

## Validation record

Initial validation was performed on 10 November 2026. The Linux reference was
extracted directly from the pinned upstream commit, without port source changes.
The extra `diffmean`, `rolloff` and `rolloffp` targets used upstream build rules;
`diffmean` needed `LDLIBS=-lnick` to correct library order without editing source.

| Setting | Linux reference | Native Windows |
| --- | --- | --- |
| Compiler | GCC 15.2.0 | MSYS2 UCRT64 GCC 16.2.0 |
| GSL | 2.8 | 2.8 |
| OpenBLAS | 0.3.32 | 0.3.34 |
| BLAS threads | 1 | 1 |
| BLAS core | NEHALEM | NEHALEM |
| Seed | 77 | 77 |

The deterministic integration suite covers 35 cases across 26 executables:
`qp3Pop`, `qpDstat` (including f4 and random subsampling), `qpF4ratio`, `qp4diff`,
`qpAdm` and `qpWave` (including automatic `qpfstats` precomputation), `qpfstats`,
`qpfmv`, `qpff3base`, `easystats`, `easycheck`, `easylite`, `convertf`, `mergeit`,
`rolloff`, `rolloffp`, `qpGraph`, `qpreroot`, `nickhash`, `grabpars`, `simpjack2`,
`dowtjack`, `diffmean`, `transpose`, `geno_single`, and `merge_transpose`.

The comparison checks both streams, exit status, and 18 generated files. Only
explicit version suffixes, executable paths/extensions, newline conventions,
temporary PIDs, addresses, CPU time, and memory measurements are normalized.
Scientific values, their printed precision, ordering, and generated files are
compared exactly; no floating-point tolerance is used. Binary transpose round
trips include LF, CR, Ctrl-Z, and 0xff payload bytes.

All 35 cases passed against the pristine Linux reference: 70 stream comparisons
and 18 generated-file comparisons matched, with no unexpected exit statuses.

Separate platform checks compare 800,000 PRNG outputs over eight seeds (including
zero and high unsigned seeds): 3,200,000 bytes, SHA-256
`b62c398efd682e2a935d20d3239103c1ea5c0b72711d4719dffc0083777bb0cc`.
They also exercise 64-bit rounding and stable ties, and sparse-file size, seek,
read-only mapping and binary I/O beyond 4 GiB. Windows-specific checks exercise
temporary directories with spaces and automatic child invocation.

See `tests/windows/README.md` for reproduction. Build provenance and hashes are
written to `bin/windows-build.json`; raw results stay in ignored
`validation-results/`. The build manifest deliberately does not certify complete
release parity.

A second compatibility pass checked gzip input and optional rendering against
the same pristine reference: 11 shared cases, 22 stdout/stderr comparisons, and
14 byte-identical genotype/graph/DOT files. Text EIGENSTRAT, packed, transposed
packed and ANCESTRYMAP inputs use concatenated gzip members. Statistics agree
across those formats, and conversions reproduce the uncompressed output bytes.
Windows additionally rejects CRC errors, truncation, plain/empty `.gz` inputs,
and handles spaces/metacharacters in genotype and rendered graph filenames.
Successful reads and decompression errors leave no decompressed temporary file.
Graphviz/Ghostscript validate the resulting PDFs; PDFs are not byte-compared
because renderer versions, fonts and metadata differ (Linux Graphviz 14.1.2 /
Ghostscript 10.06.0; Windows Graphviz 16.1.0 / Ghostscript 10.08.0).

The Python conversion/extraction/merge/hash workflow produces 12 files matching
the pristine Linux helpers byte-for-byte, including sample order, genotype
headers/hashes, SNP bytes and LF text files. Windows tests force a denied-symlink
error to exercise the copy fallback and cover paths with spaces/metacharacters.
The modified Linux C files compile, and the modified Python helpers on Linux
produce the same 12 files. The user's installed WSL checkout at
`/home/user/AdmixTools` has the same upstream HEAD and was left unchanged.

These results are in `validation-results/{windows-next-final,linux-compatibility-verified,
windows-compatibility-final,linux-script-helpers,windows-script-helpers,linux-port-script-helpers}`.
The separate runners and reproduction commands are in `tests/windows/README.md`.

## Remaining release work

- Extend scientific fixtures to the 11 build-only tools: `ascore`, `gcount`,
  `kimf`, `mkweights`, `multimerge`, `qpBound`, `qpDpart`, `qpdslow`, `qpfit`,
  `qpmix`, and `snpunion`. Their compilation does not establish numerical parity.
- Test real upstream example datasets, additional seeds, missing data, more
  genotype formats, ill-conditioned models, and large end-to-end analyses.
- Add repeatable Windows/Linux/macOS CI and decide a supported compiler and
  dependency matrix. A match on these fixtures does not establish identical
  results for every input or library combination.
- Finish auditing interpreter helpers beyond the tested Python workflow,
  including Perl/R, shell pipelines, samtools and file-linking utilities.
  Obsolete BAM/SLURM shell helpers in `nicksrc` are not called by supported tools
  and were not rewritten. Exercise Unicode/long paths and fatal-error behavior.
  Windows' native
  fatal termination codes need not equal Unix signal-derived shell codes.
- Extend compressed-input failure tests: cleanup after a fatal genotype-reader
  error, temporary-name collisions, disk-full behavior, and very large expanded
  files. Valid gzip parity is tested; arbitrary malformed-input diagnostics are
  not certified. zlib ignores trailing non-gzip bytes where GNU gzip may warn;
  pristine upstream also ignores positive `gunzip` exit statuses and invokes it
  twice. Neither behavior is a scientific calculation to copy into the port.
- Continue the per-item hard audit on the published `windows-port` branch.
  Keep `master` as the upstream tracking line; update `UPSTREAM_BASELINE` and
  rerun comparisons for each upstream synchronization.
- After the compatibility baseline is release-ready, implement the MSI milestone:
  chosen install directory, dependency/build provisioning, PATH, upgrade, repair,
  and uninstall. Optimization work follows the validated baseline.

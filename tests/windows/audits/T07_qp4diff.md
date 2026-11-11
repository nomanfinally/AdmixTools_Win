# T07 qp4diff

Status: **reviewed with open compatibility differences and deferred upstream
defects**, 12 November 2026. This is a hard-check report, not a clean tool pass
or full-suite parity certification. The scientific source was not repaired.

The oracle is unmodified upstream
`67bc219174a109951a9434e0a383ec464fb140ee`, extracted from the local Git object
database. All **112** reference C/header hashes match those objects. This audit
does not substitute a repaired Linux build. Working HEAD is `37ed02b` on the
pre-existing `audit-t03-qpwave` branch. Existing audit/restoration edits were
preserved; no branch switch, commit, push, publication or installed-bin replacement
was made. The topic branch was retained to avoid moving the user's active work.

[Machine evidence](T07_qp4diff.evidence.json) records builds, source/binary/stream
hashes, every status/result row, independent oracles, native checks, counters and
all comparison differences. [Connected modules](T07_connected_modules.md) and
the [compiler inventory](T07_modules.inventory.json) identify the actual scope.
Raw evidence is under `validation-results/hard-check/T07/`; its portable
`raw-evidence.tar.gz` and SHA-256 are recorded in the evidence JSON.

## Outcome

- Fresh native Windows matrices completed **121 cases before and after** the
  four-line Windows-only getopt correction. Pristine Linux, port Linux,
  ASan/UBSan recovery and final-source coverage matrices each completed
  **120 cases**. Windows adds Unicode paths. Completion includes expected
  failures and reproduced defects, not 121 passing tests.
- All **69 jointly successful qp4diff cases with finite rows**, containing
  **122 scientific rows**, match pristine Linux exactly at printed precision.
  All **11 independent allele/covariance/jackknife oracles** match on every
  completed matrix. No scientific tolerance or row removal is used.
- Full stream/status/generated-file comparisons: **82/121** pristine/Windows,
  **118/120** pristine/port Linux, **118/120** port Linux/coverage and **10/120**
  port Linux/sanitizer. The sanitizer differences primarily retain inherited
  hash UB diagnostics; the integer-overflow case also changes instrumented
  behavior. The two ordinary Linux/coverage differences are absolute paths
  inside failed space-path extension fixtures. None is hidden.
- Before/after Windows comparisons are **116/121 exact**, with **zero scientific
  row changes**. Differences are the two corrected getopt stderr messages and
  three echoed absolute fixture paths. Help, options, exit behavior and version
  `470.w` are otherwise retained; Linux remains `470`.
- Fifteen direct probes per native/Linux/sanitizer build cover f4/count
  boundaries, estimator lifetimes/error returns, rounding/equal-key sorting,
  **800,000 byte-exact RNG outputs**, and sparse size/seek/mapping beyond **4 GiB**.
  Both successful estimator workspaces repeat 16 times without leak reports.
  Too-few-block workspaces leak upstream allocations (F090).
- Native PowerShell **5.1.26100.9818 / AMD64**: direct invocation, parameter and
  working paths with spaces, separate streams, Tee, gzip equality, backslash
  temporary display and cleanup pass. A **293-character** temporary directory
  also passes on this machine's existing long-path policy. Packed transpose
  round trips and prepared genotype bytes match exactly across platforms.
- Tool-local coverage is **6/11 functions, 284/393 executable lines and 149/268
  branches taken**. Five legacy functions are dormant. Aborts do not reliably
  flush counters. This is explicitly not complete branch/module coverage.

## Execution contract

`main -> readcommands -> getsnps/getindivs/getgenos -> chromosome filtering ->
numlines/readpopx -> population/index construction -> setplimit/loadsnpx ->
setblocksz -> countpops -> doq4diff[/doq4diffx] -> getf4/hfix -> weightjack`.

| Surface | Actual upstream contract and tests |
| --- | --- |
| CLI | `-p`, `-v`, `-V`, `-h`; no arguments exits 1 with stderr usage. `-v` prints a version, reports `no parameters` on stderr without `-p`, then main prints another version banner and exits 0. `-v -p` continues analysis. Invalid/missing operands, missing parameters, verbose and help are tested. |
| Population list | Eight names per row, colon/comma separators, comments/blanks, ignored extra fields, repeated populations, unknown/NULL names, empty/short/long rows, long comments and 31 ordinary rows. NULL is a sentinel from getf4 but **both sides reject it** here. It is not qpF4ratio's constant denominator feature. |
| Shared-SNP mode | Default `overlap: YES`; average `firstf4mult*f4(left)-f4(right)` on jointly valid sites, with upstream weighted delete-block jackknife and `1e-10` delete-denominator addition. Count is joint SNP support. |
| Separate-SNP mode | `overlap: NO` or `allsnps: YES`; each quartet has its own mean/support, block weights sum both supports, reported SNP count is their union. `allsnps: NO` forces shared support even if `overlap: NO`. Both precedence directions and independent missing-support oracles are tested. |
| f4/missingness | `fancyf4: NO` by default. YES permits zero f4 when a fully observed contrast pair is equal and the other pair has missing calls, except cross-pair repeated-population cases. Tests cover strict/fancy, missing sites, f2/f3 covariance corrections, 24 left-quartet permutations and signed/zero/scaled firstf4mult. |
| Selection/blocks | `numchrom`, bad SNPs, physical fallback and `gfromp`, population limits, unequal blocks, zero/negative/NaN/infinite block sizes, one/two SNPs, one usable block and no surviving SNPs. Default block size is **.05 Morgans**. `blockname` is not parsed. Oracle fixtures use .5-Morgan blocks and <=.1 Morgan per chromosome, giving independently known chromosome blocks. |
| Inactive controls | `seed`, `chrom`, `xdata`, `noxdata`, `inbreed`, `jackweight`, `jackquart`, `blockname` are not parsed despite globals or support elsewhere. Parsed `nostatslim` is clamped then unused. No seeding occurs; limiting consumes the default RNG stream. The combined ignored-control fixture matches pristine/default output. |
| X | Default numchrom 22 excludes X. `chrom/xdata/noxdata` do not enable it here. `numchrom: 23` admits X; mixed, male, female and unknown-sex text inputs reproduce Linux. This is compatibility coverage, **not independent X scientific/ploidy validation**. The shared countpops path counts two alleles per called genotype. |
| Genotype I/O | Text EIGENSTRAT, packed normal/transposed, ANCESTRYMAP, PED and BED; gzip variants, concatenated members and damaged inputs. Gzipped PED/BED fail on both platforms because the decompressed name loses the format extension; do not advertise support. Valid gzip text/packed/transposed/ancestry succeeds. Missing/truncated/malformed/empty files, duplicate IDs and header errors are exercised. |
| Output | Results stay on stdout in upstream wording, order, spacing and precision; no banner/logging wrapper was added. `output/outputname` create/truncate an unused file. Single usable block produces `badoctet:` with 0, 1, 0 and -999, returning success. Zero SE prints undefined Z with differing CRT NaN spelling. |
| Helpers | No qpfstats, interpreter, graph/rank or scientific child process is called in either estimator mode. convertf/transpose are fixture preparation, not runtime subprocesses. Unix gzip uses upstream's external command twice; Windows uses shared zlib. |

## Findings and disposition

Stable existing IDs are reused for the same defect class. All upstream defects
below remain in active source as required by the compatibility-only scope.

| ID / severity / classification | Evidence and cause | Disposition |
| --- | --- | --- |
| **F044 / medium / Windows diagnostic regression, corrected** | `cli-invalid-option` originally printed `unknown option -- z`; `cli-missing-value` omitted quotes around p. Raw MinGW getopt bypassed the existing adapter. | Four guarded lines select `admix_getopt` only on Windows. Corrected stderr matches pristine after executable suffix normalization. Unix parsing and all scientific functions are untouched. |
| **F088 / high / open Windows compatibility gap; related upstream F031** | `gzip-crc` and `gzip-truncated`: pristine/port Linux exit 0 and print `0.009015 0.001354 6.658 2200`; Windows aborts without a result. Linux runs gunzip twice and only tests a negative system return, ignoring its nonzero child status. Windows `admix_gunzip` rejects the gzip error and deletes decompressed bytes. Corrupt-header diagnostics also differ. | Not dismissed as an upstream-only issue: the Windows rejection is a real deviation from the required pristine oracle. A compatibility repair must retain Linux's decompressed-byte/exit behavior in the Windows input path, including partial-output/error cases, without repairing Unix or merely weakening comparison. This shared service affects other genotype consumers and needs its own focused cross-tool patch/regression work. No such behavior change was applied during this audit. |
| **F089 / low / open platform presentation difference on undefined results** | `constant` and `zero-difference`: both platforms exit 0 with estimate/SE 0; Z is `nan` on Windows versus `-nan` on Linux. The full result lines are retained in diffs. | Not normalized away or described as finite numerical parity. Any Windows formatting fix must be narrowly proven against the pinned reference, without changing the undefined-estimate policy or suppressing result fields. |
| **F083 / high / inherited heap overwrite** | `long-list` and `long-comment` produce Windows heap corruption (`0xC0000374`); pristine Linux also aborts. ASan identifies a pointer write past the `plists` allocation in readpopx. numlines uses a much larger buffer than readpopx's 511-byte fragments, so one counted physical line becomes multiple rows. A comment continuation can become data. | Deferred. Whole-line/capacity-consistent parsing is a separate upstream repair; do not add Windows-only acceptance/rejection. Products such as nplist*8 also lack checked int bounds; enormous real lists were not allocated. |
| **F084 / high / inherited limiting/seed defect** | `limit-3`, `limit-1`, `limit-77`, `limit-123` equal default `0.009015 0.001354 6.658 2200`. A physically reduced first-three sample fixture prints `0.012172 0.002440 4.989 2200`. main builds xindex/xtypes/nrows before setplimit; countpops uses the stale index. Seed is not parsed. loadsnpx still consults ignore flags, so missing data can make the effect inconsistent. | Deferred. Do not reorder selection or activate seeds during porting. The shared RNG itself matches glibc exactly in the recorded probe. |
| **F086 / high / inherited output data loss** | `output` and `outputname` each truncate a 25-byte sentinel to zero bytes while returning success and printing results only to stdout. ofile is opened before reading inputs but never written. | Deferred. README.WINDOWS documents stdout redirection and the actual side effect. No runtime parameter rejection or new file output was introduced. |
| **F048 / high / inherited domain/overflow defects** | Zero/negative/NaN/infinite block sizes are accepted. `numchrom: 2147483647` overflows in main and mcio under UBSan; ordinary optimized Linux/Windows happen to return a result, whereas the instrumented run rejects after overflow. | Deferred; optimized agreement is not a proof of defined arithmetic or safe extreme inputs. |
| **F050/F051/F073 / medium / inherited interface/input behavior** | Duplicate individual IDs are accepted; `3oops` parses as 3; `-v` continues, output controls and many keys are misleading/inactive. Duplicate SNPs reject separately. | Preserved and documented. No duplicate-ID validator, stricter numeric parser, new control or changed exit was added. |
| **F017 / high / inherited shared hash UB** | Halt-on-error sanitizers stop preparation in xsearch xcshift/xhash1/stringhash. Recovery mode reports signed shifts/overflow in ordinary input cases, then reaches later checks. Relevant function bodies match pristine source; ordinary pristine/port data and results agree. | Deferred. Full recovery stderr remains evidence; the matrix is not called sanitizer-clean. |
| **F090 / medium / inherited estimator workspace leak** | Direct one-block probes return -999 but leak allocations on the early return: LeakSanitizer reports **144 bytes/6 allocations** for shared support and **192 bytes/8 allocations** for separate support in this optimized build. All-negative block probes expose the same exit path. Normal 16-iteration workspaces are clean. | Deferred. Cleanup before early return can be a later upstream repair with unchanged scientific returns. This is not a Windows-only ownership patch. |

The inherited X-counting concern F087 also reaches this shared countpops call;
T07's new tests establish Linux compatibility for those text cases, not an
independent sex-aware oracle. The broad repaired-Linux probes from earlier
audits cannot establish current behavior: a reused shared harness failed to
build because `reserve_temp`, `release_temp` and `loadlist_type_capacity` were
removed during scope restoration. That failed build is retained and not counted
as validation. New direct probes use the current production API.

## Architecture, build and limits

The direct native architecture is suitable for this compatibility baseline:
upstream executable/source layout, conditional version suffix, shared Windows
services, 64-bit offset/type adapters and native zlib. The getopt call-site fix
improves that boundary without introducing another parser or wrapper. A broad
rewrite would make scientific order, implicit RNG state and upstream merges
harder to verify. Dormant helpers, process-global state, duplicate local list
readers, unused workspaces/globals and narrowing an unused getgenos return into
int are maintenance concerns; they are not evidence of a new reachable Windows
calculation defect. No optimization, statistical default or dependency ABI changed.

Windows: UCRT64 GCC **16.2.0**, x86-64/LLP64, GSL **2.8**, OpenBLAS **0.3.34**,
zlib headers **1.4**; Linux: GCC **15.2.0**, x86-64/LP64, GSL **2.8**, OpenBLAS
**0.3.32**, zlib **1.3.1** package. Upstream O2/O3, `-ffp-contract=off
-fno-fast-math`, one BLAS/OpenMP thread, NEHALEM core selection and C locale are
recorded. The fixture generator seed is 1907; qp4diff does not parse its own
seed. Linux links using the additional command-line `LDLIBS=-lnick` to resolve
upstream link ordering; source is unchanged. Linux qp4diff ldd shows libc/libm;
no active estimator BLAS/GSL calculation was inferred from link inputs.

The final validated binary is
`validation-results/hard-check/T07/final-build/snapshot/bin/qp4diff.exe`.
Installed `bin/qp4diff.exe` remains the original build. Final coverage uses final
source; ordinary Linux/ASan builds precede the Windows-only getopt guard, whose
Unix preprocessed behavior is unchanged. Reproduction commands are in the
[test guide](../README.md#t07-qp4diff).

Normalization is limited to `.exe`, requested `.w`, CRLF/LF, CPU/memory/address
metadata and gzip temporary operands/quotation. Scientific rows, NaN signs,
absolute data paths, stderr and native exit codes remain visible. SIGABRT -6
and Windows fast-fail `0xC0000409` are recorded separately; heap corruption is
not treated as that ordinary fatal representation. BOM, CRLF macro and quoted
space/Unicode parameter acceptance are documented Windows input extensions.

No macOS build, native Windows sanitizer, real >4 GiB genotype, every large
dimension/offset product, UNC/policy combination, interrupted process, allocation
failure or forced mapping failure was certified. The sparse probe tests platform
I/O/mapping, not all genotype-reader arithmetic. Five dormant local functions,
unflushed fatal branches and independent M/H/Q contracts remain open. All T07,
module and header checkboxes remain unchecked. The audit found useful finite
parity evidence and one corrected diagnostic regression; **F088/F089 prevent an
unqualified compatibility pass**.

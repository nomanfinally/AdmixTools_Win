# T02 qpfstats: corrections to retained upstream defects

Status: **passed with limitations**, 10 November 2026. Findings F034, F035,
F039, F040 and F041 are corrected following the request to fix the defects
retained in the initial review. F042, a duplicate-name diagnostic defect found
while implementing these checks, is also corrected. No requested finding remains
open. This closes T02 within the tested scope; other tools and shared modules
retain their independent audit status.

The [initial report](T02_qpfstats.md) and
[initial evidence](T02_qpfstats.evidence.json) remain historical records.
The [correction evidence](T02_qpfstats.corrections.evidence.json) records current
source hashes, environments, individual cases, comparisons and artifact hashes.
Working base is `ff2029d`; changes are uncommitted on `fix-t02-defects`.
Upstream reference remains `67bc219174a109951a9434e0a383ec464fb140ee`.
The pristine Linux tree was not patched. Corrected Linux and sanitizer builds
use isolated trees; raw evidence is in `validation-results/hard-check/T02/`.

## Repairs and intentional compatibility changes

| Finding | Correction | Verification / compatibility consequence |
| --- | --- | --- |
| F034 | Apply population sampling before building the analysis index and calculating SNP weights. Counts and calculations now use the same selected individuals. | With nine six-person populations, limit 3 selects 27 analysis rows. For seeds 77 and 123, output matches an independently constructed physical subset byte-for-byte. Unlimited sampling retains the ordinary baseline bytes. Limited output deliberately differs from pristine upstream, which analyzed all 54 rows. |
| F035 | Initialize the existing RNG using qpfstats's parsed seed before sampling. No RNG algorithm or sampling algorithm changed. | Repeat runs match; seeds 77/123/high-bit affect selected results and match Windows/Linux. Seed 0 retains the implicit default sequence, equivalent to 1. Parameter-file seed continues to override CLI `-s`. A seed has no scientific effect when no random-dependent operation is requested. |
| F039 | Remove qpfit's unconditional successful exit before fitting. Initialize its existing bootstrap RNG, read effective blocks from the fstats header, handle a single source, and reject invalid source/right-population/bootstrap dimensions before allocation. | Cached and automatic fits now produce rank tests, coefficients, standard errors and summaries. Single/three-source, ratio and high-resolution modes pass against corrected Linux and ASan/UBSan. Pristine qpfit cannot provide numerical fitting parity: the original code never executed this path and its prototype conflicts with the current header. This restores the existing algorithm rather than introducing a replacement estimator. |
| F040 | Share qpfstats helper preparation, execution, copying and ownership across qpAdm, qpWave, qpfit and qpGraph. Reserve names exclusively, track owned files, and clean them on normal exit, fatal errors and helper/copy failures. POSIX execution uses fork/exec instead of shell commands; Windows retains native sibling execution. | All four callers pass automatic/explicit output/log, missing-helper/temp-directory and copy-failure checks. Collision probes preserve an existing sentinel. `keeptmp` preserves all five files, including on failure, for callers that support it; qpGraph gains no new option. Explicit user output/log files are preserved. Fatal cleanup also works with an open read handle on Windows. Forced termination/power loss remains untested. |
| F041 | Correct help; explicitly reject unused `-g/-o/-x` and ten known inactive direct parameter keys. Require unique individual IDs and finite positive block size. | Each rejection has a regression case. Unsupported keys are `doanalysis`, `quartet`, `fstdmode`, `useweights`, `diag`, `minvar`, `nostatslim`, `f3log`, `root`, `output`. Parent helpers remove those parent-only fields before launching qpfstats, preserving automatic parent analyses. Unknown keys generally retain upstream parser behavior; this is not universal typo detection. Use `fstatsoutname:` and shell redirection. |
| F042 | Return the original input index from shared `finddupalt`, rather than a position in its sorted index array. | Input `z,z,a` previously reported index 2/name `a`; it now reports index 0/name `z`. The shared diagnostic repair affects duplicate-name callers, not statistical calculations. M07/H30 remain pending independent reviews. |

These are explicit upstream behavior repairs, applied to both Windows and the
corrected Linux comparison build. They must not be advertised as exact agreement
with broken pristine behavior. No new algorithm, optimization, precision,
calculation reassociation or statistical default was introduced. Version remains
qpfstats `1101` / Windows `1101.w`; qpfit retains its existing terminal wording.

## Final recorded validation

All 37 native Windows targets rebuilt with UCRT64 GCC 16.2.0, GSL 2.8,
OpenBLAS 0.3.34 and zlib 1.4. Linux uses x86-64 GCC 15.2.0, GSL 2.8 and
OpenBLAS 0.3.32. Existing strict floating-point flags, 64-bit offsets and Windows
8 MiB stack are retained. Single-thread dependency settings and exact compiler,
linker, source and binary details are in the correction evidence. ASan/UBSan
uses a separate Linux non-PIE build with halt-on-error and leak detection disabled.

| Check | Observation |
| --- | --- |
| Composed native Windows / corrected Linux / ASan+UBSan matrices | 185 / 183 / 183 unique cases; all behavior/cleanup checks pass; no invalid-access or UB finding |
| Shared Linux/Windows cases | 181; all 106 jointly successful cases match stdout, stderr and requested helper logs exactly after narrow metadata substitutions |
| All shared streams, including failures | 360/366 exact; the remaining six differences are the same five recorded platform cases: BOM acceptance, corrupt/truncated gzip errors, output-directory errno and truncated packed-input zero-errno wording |
| Case/file hashes | 129/130 exact; only BOM acceptance produces a file on one side. These include retained inputs and are not 130 distinct generated datasets. |
| Full verbose output | All 3,108,709 stdout lines compared with Linux and ASan; only version, CPU and memory metadata differ. Generated fstats bytes match. |
| Population subset oracle | Seeds 77/123 match explicitly subsetted genotype/individual files byte-for-byte on all three builds |
| 35-case cross-suite regression | 69/70 streams exact against pinned pristine Linux; only the previously documented F037 population diagnostic differs. All 18 generated files and binary round trip match exactly. |
| Focused qpAdm reruns | Windows 22 cases and Linux ASan 17 cases pass, including automatic helper lifecycle and failure handling; Windows also exercises Unicode paths and long log paths |
| Shared ownership/dimension probes | 16 Windows and 16 ASan cases pass, including collision, fatal cleanup, keep behavior and duplicate-name index |
| Native PowerShell 5.1 | Direct redirection and Tee-Object both exit 0; generated fstats hash matches the runner and pristine default |
| Pristine identical-input follow-up | Default, explicit defaults and unlimited-limit fstats bytes remain unchanged; limited/seed-selected calculations intentionally change. Inactive keys/switches, duplicate IDs and invalid block sizes now fail explicitly. |

No floating-point tolerance or scientific-line filtering is used. Narrow
metadata rules are described in the initial report. The new shared helper also
requires unquoting only generated `fstatsoutname`/`poplistname` PID paths when
comparing Windows parameter echoes to Linux. Native abort statuses remain
different and recorded. Full matrices precede the final POSIX copy-error wording
change; the final helper matrices supersede every affected case. Case origins
are explicit in the evidence, and incomplete runs cannot verify as successful.

## Reproduction and limits

Use new output directories for each run, with identical fixtures and controlled
dependency/thread settings on Windows and isolated Linux builds:

```powershell
.\build-windows.ps1 -Msys2Root C:\msys64
python tests/windows/audit_qpfstats.py --bin bin --output validation-results/T02-corrected-windows
python tests/windows/audit_qpfstats.py --verify validation-results/T02-corrected-windows
python tests/windows/audit_qpfstats.py --compare validation-results/T02-corrected-linux validation-results/T02-corrected-windows
```

`--select REGEX` runs selected cases. To run the physical-subset oracle, compile
`tests/windows/qpfstats_probe.c` against the real qpfstats dependency objects
(excluding `qpfstats.o`), libnick and scientific libraries, then pass `--probe
PATH`. The probe includes qpfstats source with its main renamed; it is a test
binary, not a new installed executable. Its `sample` mode prints selected input
indices; the Python runner builds subsetted files preserving original row order.
The retained local `run_probes.py` records both platform link commands.

Coverage remains synthetic and specific to the recorded toolchains. No real
cohort, macOS runtime, network/UNC path, forced termination, power/disk loss,
exhaustive allocation failure or every finite numeric input is certified.
Leak detection is disabled; explicit owned-file lifecycle assertions are not a
whole-process leak-free guarantee. The earlier sparse >4 GiB probes exercise
shared native services, not a full multi-gigabyte qpfstats cohort. Windows long
paths were tested under this machine's enabled policy. qpfit and the other
consumers still require their full independent hard audits before suite-wide
claims are appropriate.

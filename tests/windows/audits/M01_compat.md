# M01: Native platform services — independent review

Scope notice (11 November 2026): this is historical audit evidence.
Inherited-bug repairs described here are not the current porting baseline.
See [the project-wide restoration](PORT_ONLY_SCOPE_RESTORATION.md) for
active sources, retained Windows adaptations and new reference results.

Follow-up: [requested T04 repairs](T04_qpDstat.corrections.md) correct the
recorded defects in their reproduced scopes; current source hashes and regression
evidence are linked there. The review below describes the original snapshot.
Independent module/header completion remains pending.

Status: **reviewed; independent contract coverage incomplete; not passed**.
Date: 10 November 2026. No production repair was made.

## Contract and source

`src/win32/compat.c`; SHA-256 `947e0b3025918efc4363e8362f9af9f9daa0d81e14ed2b11845b08a8acebc69a`.
RNG, binary I/O, line reading, environment, owned temps, gzip, native processes, mapping and diagnostic metrics.

The pinned upstream and current port baseline, actual build commands, dependency
versions/ABI, environments, raw per-case statuses and archive hash are in
[T04 evidence](T04_qpDstat.evidence.json). Caller/reference candidates and every
compiler-recognized function are in [the function inventory](T04_modules.inventory.json).
Archive membership/reference matches do not establish runtime reachability.

Header closure: `H38` src/win32/compat.h.
These headers compile in their real production contexts; standalone header
self-containment, every default/table and every inactive platform branch are
not thereby certified. H items remain open.

## Recorded checks

| Contract check | Evidence and limit |
| --- | --- |
| Ordinary and numerical behavior | Direct cases `M01-io`, `M01-sibling`, `M01-process-errors`, `M01-services`, `M01-M06-M08-platform`, `M01-rng`, `M01-largefile`; ordinary/mode consumers in T04. Exact output comparison retains discrepancies. |
| Results, streams, files and exits | All raw stdout/stderr/statuses retained; RNG stdout is compared as binary bytes, packed files by SHA-256. OS abort codes are retained. No scientific tolerances. |
| Boundary/malformed input | Direct boundary cases plus T04 input/block/chromosome/format matrix. This is not exhaustive for unexecuted functions. |
| RNG and calculation order | Fixed fresh-process seeds, single-thread dependencies, no fast-math/reassociation; no algorithm change. For non-random functions this row applies only to their random-dependent callers. |
| Widths, ABI and large offsets | Native 64-bit build, 64-bit port offset type, 32-bit BLAS integers; >4-GiB service probe and ordinary genotype round trips. No end-to-end >4-GiB scientific run. |
| Paths, helpers and ownership | Native PowerShell/path/gzip matrix, shared qpWave helper regressions and relevant direct probes. No filesystem/process behavior is inferred for pure numerical functions. |
| Memory and lifetime | Linux ASan/UBSan, selected leak detection, native Windows ordinary/failure probes. First-failure aborts and missing Windows MSan/ASan limit conclusions. |
| Non-Windows and affected callers | Pristine Linux and current Linux builds, targeted sibling cases; macOS not executed. Caller tool IDs retain their independent audit status. |

## Coverage, findings and closure

Not instrumented on Windows; Linux does not build M01.
Compiler warning inventory: 1 warnings under the recorded
extra review flags. Warnings alone are not findings or passes.

For findings, severity, reproducer, platform behavior and proposed repairs, see
[the T04 finding register](T04_qpDstat.md#findings). Existing corrected findings
retain their original IDs and scoped historical status.

**Remaining:** Graph rendering, storage/permission failure combinations, forced termination, handle inheritance isolation and exhaustive allocator-failure injection remain unverified.

Functions without a recorded positive Linux execution count:
`admix_getopt`, `owns_temp`, `admix_open`, `admix_fopen`, `admix_track_temp`, `admix_release_temp`, `admix_cleanup_temps`, `admix_reserve_temp`, `admix_setenv`, `admix_random`, `admix_srandom`, `admix_initialize_io`, `admix_getline`, `admix_tempdir`, `admix_cpu_seconds`, `admix_memory_bytes`, `admix_filter_fstats`, `admix_copy_file`, `admix_gunzip`, `append_argument`, `run_program`, `admix_run_sibling`, `find_program`, `admix_render_graph`, `admix_run_qpfstats`

No module/header is closed by the T04 tool review. Completing the remaining
contracts requires additional evidence; these limitations are not a clean pass.

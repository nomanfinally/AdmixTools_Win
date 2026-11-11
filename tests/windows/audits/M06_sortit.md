# M06: Sorting and medians — independent review

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

`src/nicksrc/sortit.c`; SHA-256 `fbdb91aa7dc850bb9d1d87809ce4dd75fa047ab7f9096c1278fab1188ab4062a`.
Integer/double equal-key ordering, zero-length rejection, finite medians and short-median allocation lifetimes.

The pinned upstream and current port baseline, actual build commands, dependency
versions/ABI, environments, raw per-case statuses and archive hash are in
[T04 evidence](T04_qpDstat.evidence.json). Caller/reference candidates and every
compiler-recognized function are in [the function inventory](T04_modules.inventory.json).
Archive membership/reference matches do not establish runtime reachability.

Header closure: `H19` src/nicksrc/admix_types.h, `H25` src/nicksrc/sortit.h, `H27` src/nicksrc/strsubs.h, `H29` src/nicksrc/vsubs.h.
These headers compile in their real production contexts; standalone header
self-containment, every default/table and every inactive platform branch are
not thereby certified. H items remain open.

## Recorded checks

| Contract check | Evidence and limit |
| --- | --- |
| Ordinary and numerical behavior | Direct cases `M06-sort`, `M06-empty`, `M06-median-leak`; ordinary/mode consumers in T04. Exact output comparison retains discrepancies. |
| Results, streams, files and exits | All raw stdout/stderr/statuses retained; RNG stdout is compared as binary bytes, packed files by SHA-256. OS abort codes are retained. No scientific tolerances. |
| Boundary/malformed input | Direct boundary cases plus T04 input/block/chromosome/format matrix. This is not exhaustive for unexecuted functions. |
| RNG and calculation order | Fixed fresh-process seeds, single-thread dependencies, no fast-math/reassociation; no algorithm change. For non-random functions this row applies only to their random-dependent callers. |
| Widths, ABI and large offsets | Native 64-bit build, 64-bit port offset type, 32-bit BLAS integers; >4-GiB service probe and ordinary genotype round trips. No end-to-end >4-GiB scientific run. |
| Paths, helpers and ownership | Native PowerShell/path/gzip matrix, shared qpWave helper regressions and relevant direct probes. No filesystem/process behavior is inferred for pure numerical functions. |
| Memory and lifetime | Linux ASan/UBSan, selected leak detection, native Windows ordinary/failure probes. First-failure aborts and missing Windows MSan/ASan limit conclusions. |
| Non-Windows and affected callers | Pristine Linux and current Linux builds, targeted sibling cases; macOS not executed. Caller tool IDs retain their independent audit status. |

## Coverage, findings and closure

10/18 Windows-inventory function names executed in the instrumented Linux run. Platform/compiler conditionals can change this denominator.
Compiler warning inventory: 22 warnings under the recorded
extra review flags. Warnings alone are not findings or passes.

For findings, severity, reproducer, platform behavior and proposed repairs, see
[the T04 finding register](T04_qpDstat.md#findings). Existing corrected findings
retain their original IDs and scoped historical status.

**Remaining:** Custom setorder/pointer/string ordering and nonfinite comparator semantics need additional contracts. No new tie policy is proposed here.

Functions without a recorded positive Linux execution count:
`median`, `lsortit`, `lcompit`, `invperm`, `compiarr`, `comparr`, `mkirank`, `mkrank`

No module/header is closed by the T04 tool review. Completing the remaining
contracts requires additional evidence; these limitations are not a clean pass.

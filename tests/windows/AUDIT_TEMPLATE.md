# <ID> — <tool/module>

Status: pending / in progress / blocked / passed with limitations / passed

Source paths and snapshot hashes:
Upstream reference commit:
Windows/Linux executable hashes:
Build commands, flags, architecture and dependency versions/ABI:
Seed, threads, locale and environment:
Related tool/module/header IDs:
Raw artifacts: `validation-results/hard-check/<ID>/`

## Contract

Record supported options, parameters, defaults, file formats, stdout/stderr,
generated files, helper commands, ownership/lifetime and exit behavior.
Identify platform guards and changes from pristine upstream. For a module,
identify callers and invariants. Link the source/documentation supporting this.

## Checks and evidence

Each row needs a reproducer/command and actual observations. Use justified N/A
for inapplicable checks. Previous fixture success does not fill a row by itself.

| Check | Fixture/command | Linux observation | Windows observation | Outcome / artifact |
| --- | --- | --- | --- | --- |
| Ordinary scientific/function behavior | | | | |
| Exact printed results and output ordering | | | | |
| Byte-identical generated scientific data | | | | |
| CLI/help/version/defaults/exit status | | | | |
| Minimal/boundary/degenerate inputs | | | | |
| Malformed/truncated/missing inputs | | | | |
| Duplicate IDs/populations and missing data | | | | |
| Seed/RNG/order and floating-point settings | | | | |
| Integer widths/ABI/large offsets | | | | |
| Paths/encoding/PowerShell/pipes/redirection | | | | |
| Helpers, environment, errors and cleanup | | | | |
| Memory, undefined behavior and lifetimes | | | | |
| Linux/macOS build paths and guards | | | | |
| Regressions in affected callers | | | | |

## Findings

For every finding, record its stable F ID, severity/impact, minimal input,
commands, expected versus actual behavior, raw output/exit status and cause.
Classify Windows regression, upstream defect, dependency/platform difference,
unsupported feature or harness defect. An upstream bug is still an open finding.
Document the smallest proposed/applied fix and its scientific consequences.

## Fixes and regression evidence

List changed files, why the change is compatibility/bug work, and the tests
showing the failure is corrected without altered calculations/defaults/output.
Record any deliberate behavior change relative to a broken upstream case.
List every normalization individually and justify it; no scientific tolerances.

## Closure

- Applicable checks completed:
- Remaining failures, limitations and blockers:
- Related items invalidated or requiring recheck:
- Final outcome and evidence:

Update both `COMPATIBILITY_AUDIT.md` and `tests/windows/audit_inventory.json`.
Do not mark a clean pass while applicable failures remain. Do not commit or push
unless requested.

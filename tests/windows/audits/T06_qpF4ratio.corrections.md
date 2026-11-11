# T06 qpF4ratio corrections

Scope notice (11 November 2026): this is historical audit evidence.
Inherited-bug repairs described here are not the current porting baseline.
See [the project-wide restoration](PORT_ONLY_SCOPE_RESTORATION.md) for
active sources, retained Windows adaptations and new reference results.

**Historical experiment, no longer applied.** The user's subsequent scope
clarification defers inherited Linux bug fixes. These changes were removed from
active production source and binaries; only the Windows getopt fix remains.
See [scope restoration](T06_scope_restoration.md). Results below describe the
retained corrected-Linux experiment, not current compatibility behavior.

Status: **all nine open finding groups corrected in their tested scopes;
passed with limitations**, 11 November 2026. The original
[audit](T06_qpF4ratio.md), [evidence](T06_qpF4ratio.evidence.json) and module
inventory remain historical. These corrections intentionally repair inherited
bugs; they do not assert full-suite parity or close independent module audits.

[Correction evidence](T06_qpF4ratio.corrections.evidence.json) retains source,
executable, input/stream/status hashes, oracle answers, original/pristine
scientific changes, consumer checks and installed provenance. The final
verifier failure list is empty.

## Repairs

| Finding | Corrected behavior |
| --- | --- |
| F044 | The existing Windows getopt adapter supplies Linux-style option-error wording. Unix getopt remains unchanged. |
| F048 | Nonpositive/nonfinite block sizes and numchrom values that cannot represent X/Y reject before genotype loading. Signed f4 denominators remain supported. |
| F050 | Individual IDs are checked before genotype loading, including packed/transposed/ancestry/PED/BED inputs. PED identity is its family/individual pair. |
| F051 | Version prints once and exits, including combined version/parameter arguments. The inactive nostatslim control rejects explicitly; parameter handles close. |
| F080 | Undefined global denominators, nonfinite delete-block estimates, nonfinite estimates/SE/Z and zero SE reject before printing the affected scientific row. Valid negative denominators and upstream delete-block epsilon/order remain unchanged. A valid A component can precede a B failure in diffmode, preserving upstream output order; no undefined B/diff row is emitted. |
| F083 | Population rows use one capacity-checked growing pointer table instead of inconsistent pre-count/read buffer sizes. Physical lines longer than 512 bytes reject without interpreting continuations as rows. Exact-size LF/CRLF/EOF boundaries, malformed later rows, table growth, read/close failures and int-product bounds are handled. |
| F084 | Population limiting precedes analysis-index construction. The existing RNG is seeded once using default seed 0; the existing seed parameter is now honored. Fixed-seed runs match physically selected datasets, including zero/one/high-bit seeds and repeats. No RNG or permutation algorithm changed. |
| F085 | diffmode must be boolean and paired lists must have an even, nonzero row count. First-half/second-half pairing and alpha A + alpha B - 1 remain unchanged. |
| F086 | Inactive output/outputname controls reject before any file is opened for writing. Existing outputs and an output/input-name collision are preserved. Results continue to use stdout. |
| F087 | qpF4ratio uses countpopsx; that shared counter now applies haploid treatment only on X. F is diploid; M/U use the established haploid convention and exclude heterozygotes. getf4 computes only needed overlap corrections, skips sites with an unestimable single-chromosome overlap, and permits a single chromosome in a nonoverlapping population. |
| Additional F060 occurrence | The dormant local banker helper uses bounded quartet membership checks instead of a 100-element stack array. Index/type validation and a 101-population probe cover it. No new executable mode is introduced. |

The shared changes are confined to countpopsx and getf4 in qpsubs. qpDstat calls
countpopsx only for its explicit X mode, so the added chromosome guard preserves
that caller's convention. Other getf4 consumers are covered by direct overlap
boundary probes and scoped qpAdm/qpWave/qpfstats/qp4diff regressions.

## Validation records

The repair matrix has 225 cases, including 50 independent oracle cases:
autosomal/f2/f3/reciprocal/permutation/unequal-block/diff estimators; seven X
text scenarios; mixed/male/female/unknown and repeated-population X scenarios
after packed, transposed, ancestry, PED and BED conversion; seeded physical
subsets; malformed inputs, parser boundaries and output preservation.

- All **225 cases on each of Windows, corrected Linux and ASan/UBSan** pass
  behavior checks. All **50 independent oracle cases** pass on every build.
- All **112 jointly successful scientific-result cases** agree at printed
  precision across Windows/Linux/sanitizers. Binary genotype round trips are
  byte-exact. No numerical tolerance was added.
- Full normalized stream/status/file comparisons are **159/225** Windows/Linux
  and **223/225** Linux/ASan. Remaining differences retain raw OS abort statuses,
  absolute paths and Windows BOM/quoted-path extensions. The two Linux/ASan
  differences are path operands. No scientific rows differ in jointly successful
  cases.
- Shared modules: **80 Windows / 78 Linux / 78 sanitizer** cases pass. Eleven
  direct production-function probes pass per build, with leak detection enabled.
- Shared consumers pass **145 qpDstat**, **11 selected qpAdm**, **14 selected
  qpWave**, and **12 selected qpfstats** cases on each build. Counts include
  preparation jobs; these are scoped regressions rather than new tool audits.
- Native and installed PowerShell checks pass, as do installed default, seeded,
  mixed-X, male-f2 and version checks. All 37 supported native binaries rebuild.

Eleven direct probes include large allele cells, insufficient haploid overlap,
single nonoverlapping chromosomes, autosomal/X indexed counting, ratio/diff
workspace lifetimes repeated 16 times with LeakSanitizer enabled, invalid block
indices, undefined difference estimates and the legacy helper boundaries.

Original Windows and pristine Linux records remain unchanged. Only population
limits/seeds, X calculations and truthful version-exit behavior are expected to
change jointly successful scientific rows. Invalid controls, duplicate IDs,
overlong lists and undefined estimates now reject. Scientific comparisons use
printed tokens exactly; no tolerance, NaN-sign suppression or result-line
deletion is used.

The 12 changed jointly successful original/pristine cases are four limit cases,
seven X cases and combined version/parameter invocation, which now exits before
analysis. Invalid/undefined cases instead reject. Exact before/after rows and
actual statuses remain in evidence. Build settings retain disabled fast-math/
reassociation, the existing PRNG and unchanged BLAS integer ABI. Ordinary
autosomal calculations and output format remain upstream.

Raw corrections are under validation-results/hard-check/T06/repairs. The final
authoritative matrix directories are completed-windows, completed-linux and
completed-asan. Earlier windows/verified/closed directories contain fixture
diagnostics or interrupted runs and are not closure evidence. Two test-fixture
repairs use format-appropriate metadata extensions and full PED identifiers.
Managed WSL/script execution initially required approved command execution;
no execution-policy setting was changed.

Fresh Linux/ASan trees are under repairs/linux-trees inside the workspace. The
pristine reference remains the original pinned build. Shared Unix closure runs
are shared-completed-linux/asan; native records are shared-windows. All raw
repair data stays in the workspace. The original review archive is untouched.

All 37 supported Windows binaries were rebuilt after native checks. The 98
previous installed files and their hashes are preserved in installed-before
and installed-before.json. Installed ordinary/seed/X/version checks and native
PowerShell checks are recorded separately. No commit, push or release was made.

Research datasets, macOS, real >4 GiB genotype files, exhaustive fault injection
and independent M/H/Q contracts remain uncompleted. Passing these corrections
does not certify those scopes or the complete suite.

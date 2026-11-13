# ADMIXTOOLS Windows port

## Primary contract

- Adapt every upstream executable for native 64-bit Windows, callable directly
  from PowerShell. Keep the upstream executable names (with `.exe` on Windows),
  command-line options, parameter files, defaults, and exit behavior.
- The Windows adaptation must give the same numerical results as the Linux
  version built from the same upstream commit. Preserve algorithms, calculation
  order, random-number sequences for a fixed seed, and scientific defaults.
- Terminal output must look the same as upstream: retain wording, spacing,
  precision, result ordering, stdout/stderr routing, and redirection behavior.
  Do not add banners, colors, progress displays, wrappers, or automatic logging.
- Append `.w` to each existing executable version code only on Windows, for
  example `2203.w`. Track the actual upstream code; do not reset all programs to
  one version. Preserve Linux/macOS version strings.
- Numerical and output parity are release requirements, not assumptions based
  on a successful build. Never advertise complete or bit-for-bit parity without
  recorded comparisons against a pinned Linux reference.

## Scope and maintenance

- Preserve upstream's repository layout (`src/`, `src/nicksrc/`, `perlsrc/`,
  examples, documentation, and installed `bin/`). Keep changes small and easy to
  review and merge when synchronizing with DReichLab/AdmixTools.
- Keep Linux and macOS build paths working. Isolate Windows compatibility code
  behind platform guards and prefer shared compatibility helpers to repeated
  changes in scientific code.
- First deliver a direct, analogous port of the full suite. Defer new algorithms,
  optimizations, SIMD, parallelism, data formats, unified dispatchers, and changed
  statistical defaults until the compatibility baseline is validated.
- This stage fixes Windows porting differences only. If a defect also occurs in
  the pristine, pinned Linux version, record it as an inherited upstream issue
  and defer its repair. Preserve inherited scientific results, CLI quirks,
  parameter acceptance, defaults and exit behavior; a bug audit is not permission
  to correct Linux behavior during this phase.
- Presentation improvements may clarify help, documentation and Windows path or
  OS diagnostics. Do not change runtime behavior to make it agree with help text,
  and do not alter scientific result wording, ordering or precision.
- Earlier upstream-bug repairs must be tracked separately from compatibility
  work. Do not describe them as porting fixes or use their successful tests to
  claim parity with unmodified Linux. Preserve their evidence and existing user
  work when separating them from the compatibility baseline.
- Other ports may inform the analysis of Windows APIs and build issues. Do not
  adopt their repository restructuring, optimizations, or claims of parity.
  Check licensing and preserve required attribution before reusing any code.
- Develop and commit the port on this fork's default branch, `main`. Keep
  `master` as the separate upstream tracking line; optional topic branches may
  be used for individual changes. Record the upstream
  commit for each release and merge upstream updates instead of rewriting history.
- Windows-incompatible upstream filenames may be renamed narrowly in place;
  preserve file bytes and update references. Document the mapping and rationale.
- Preserve existing user changes. Do not commit, push, or publish a release unless
  the user requests it.

## Validation

- Use `COMPATIBILITY_AUDIT.md` and `tests/windows/audit_inventory.json` as the
  per-tool/module hard-check queue. Existing build/parity fixtures are prior
  evidence, not completed hard audits. Keep IDs stable, record findings and
  regression cases, and finish each item's applicable checks before marking it
  passed. Preserve the distinction between Windows regressions and upstream bugs.
- Inventory all upstream default/install executables, additional buildable tools,
  and interpreter-based helpers. Track gaps explicitly; do not equate a subset
  with the full suite.
- Compare a pristine, pinned Linux build and the Windows build on identical
  inputs, parameter files, fixed seeds, and controlled dependency/thread settings.
  Record compiler, flags, architecture, GSL/BLAS versions, and reference commit.
- The pristine Linux build is the compatibility oracle. A separately repaired
  Linux build may diagnose a finding, but agreement with it does not establish
  compatibility with upstream. Record inherited failures without treating their
  correction as a requirement for a Windows porting pass.
- Compare scientific numbers and generated data, help/version text, stdout,
  stderr, and exit status. Test binary genotype round trips, memory mapping,
  random-dependent analyses, helper subprocesses, paths with spaces, and large
  file offsets (Windows uses LLP64, unlike Linux LP64).
- Compare deterministic output exactly at upstream's printed precision and binary
  data byte-for-byte. Never hide scientific differences behind broad floating
  point tolerances or remove result lines. Any exception must be narrowly scoped,
  justified, and documented. Timing, memory usage, addresses, paths, newline
  conventions, and the requested `.w` suffix can differ in value, while retaining
  upstream's output format.
- Use native backslashes for generated Windows filesystem paths, including
  temporary paths printed in the terminal. Preserve Unix path formatting on
  Linux/macOS and continue accepting forward slashes in Windows input paths.
- Avoid fast-math, reassociation, CPU-specific optimizations, changed PRNGs, or
  silently different BLAS integer ABIs. Investigate numerical differences before
  changing tolerances. Report what was actually tested and what remains untested.

## Documentation and packaging

- Public files and commit history must not include a contributor's personal
  name, email, Windows profile, machine name or absolute workspace/toolchain
  location. Use variables, relative paths or clearly generic examples. Public
  GitHub handles and upstream attribution may remain.
- Keep `README.WINDOWS.md` general. Generate machine-specific instructions as
  `README.WINDOWS.personal.md` with `New-PersonalWindowsGuide.ps1`; this file and
  `.private/` must remain ignored. Never force-add personal guides or recovery
  copies. Before publishing, check staged text and metadata for personal paths,
  including nested JSON strings in audit evidence.
- Maintain `README.WINDOWS.md` as a reproducible beginner-friendly tutorial:
  prerequisites, checkout, build, dependencies, PowerShell usage, parameter/data
  paths, output redirection, persistent user PATH, verification, troubleshooting,
  upgrades, and uninstall instructions. Label unverified steps clearly.
- Keep Windows build and validation instructions current with implementation.
- A standard MSI installer is a later milestone after parity: user-selected
  installation location, dependency/build provisioning, PATH integration, repair,
  upgrade, and clean uninstall. Do not claim an installer exists before it does.

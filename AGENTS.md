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
- Other ports may inform the analysis of Windows APIs and build issues. Do not
  adopt their repository restructuring, optimizations, or claims of parity.
  Check licensing and preserve required attribution before reusing any code.
- Keep `master` as the upstream tracking line and develop the port on
  `windows-port`; use small topic branches for later changes. Record the upstream
  commit for each release and merge upstream updates instead of rewriting history.
- Windows-incompatible upstream filenames may be renamed narrowly in place;
  preserve file bytes and update references. Document the mapping and rationale.
- Preserve existing user changes. Do not commit, push, or publish a release unless
  the user requests it.

## Validation

- Inventory all upstream default/install executables, additional buildable tools,
  and interpreter-based helpers. Track gaps explicitly; do not equate a subset
  with the full suite.
- Compare a pristine, pinned Linux build and the Windows build on identical
  inputs, parameter files, fixed seeds, and controlled dependency/thread settings.
  Record compiler, flags, architecture, GSL/BLAS versions, and reference commit.
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
- Avoid fast-math, reassociation, CPU-specific optimizations, changed PRNGs, or
  silently different BLAS integer ABIs. Investigate numerical differences before
  changing tolerances. Report what was actually tested and what remains untested.

## Documentation and packaging

- Maintain `README.WINDOWS.md` as a reproducible beginner-friendly tutorial:
  prerequisites, checkout, build, dependencies, PowerShell usage, parameter/data
  paths, output redirection, persistent user PATH, verification, troubleshooting,
  upgrades, and uninstall instructions. Label unverified steps clearly.
- Keep Windows build and validation instructions current with implementation.
- A standard MSI installer is a later milestone after parity: user-selected
  installation location, dependency/build provisioning, PATH integration, repair,
  upgrade, and clean uninstall. Do not claim an installer exists before it does.

# Development installer validation — 14 November 2026

Artifact: `AdmixTools-8.1.0-windows-x64.msi` (55,383,652 bytes).

SHA256: `ffacdf6f019320758cdfda11057054a98d9b4ce41060769d086a43f0a3231310`.

The exact artifact completed the automated installer lifecycle test on native
x64 Windows build 26300, using Windows PowerShell 5.1. This records one machine's
results, not certification of every supported Windows version or configuration.
See [the machine-readable summary](VALIDATION.json).

| Check | Result |
| --- | --- |
| WiX 6.0.2 compilation and MSI validation | Passed, no reported validation warnings |
| x64 MSI, embedded cabinet, generic package author | Confirmed |
| Custom directories containing spaces | Passed with PATH unchecked and checked |
| Installed payload | All 506 files match manifest SHA256 values in both cases |
| User PATH | Optional entry added once; repair does not duplicate it; uninstall restores the original value |
| Machine PATH | Unchanged |
| Offline runtime smoke checks | qpAdm help, Graphviz and Ghostscript run with a minimal process PATH |
| Rendering | Actual DOT → PostScript → PDF conversion passes |
| Automatic helper lookup | qpreroot produces a PDF with only System32 on process PATH; bundled helpers are found beside the executable |
| Repair | Deliberately damaged qpAdm executable restored to its exact original hash |
| Uninstall | Installed executable removed; user-created file preserved |
| Restart handling | Every final install/repair/uninstall exits 0; restart/application-shutdown suppression authored and explicitly passed by the test |
| Portable ZIP | ZIP CRCs and artifact manifest checksums pass |
| Runtime import closure | All 98 PE files inspected; remaining direct imports are Windows/UCRT components |
| Public payload privacy | Profile-path scan passes; personal guide and raw logs excluded |

The 37 native AdmixTools binaries used in this package were also rerun through
the existing 35-case integration suite. Against the previously recorded pristine
Linux reference at `67bc219174a109951a9434e0a383ec464fb140ee`, all 70 normalized
streams and 18 generated files match; both binary round trips are exact. Only
the existing, narrowly defined metadata substitutions are applied. This does
not establish numerical parity for every executable or mode.

An earlier candidate exposed unsafe restart handling during forced repair.
The package now authors `REBOOT=ReallySuppress` and
`MSIRESTARTMANAGERCONTROL=Disable`; tests also pass both explicitly and use
explicit reinstall properties. The delivered artifact passed both complete
lifecycle cases after this correction.

## Remaining validation

- Native wizard artwork was visually inspected; dialog routing and options were
  checked in the MSI database. A live desktop wizard walkthrough, accessibility
  review and high-DPI presentation check remain unperformed.
- A separate clean Windows computer/VM, older supported Windows versions,
  ARM64 emulation and enterprise policies have not been tested.
- Major-upgrade preservation and downgrade blocking are authored but have not
  been exercised between two separately versioned packages.
- The MSI is unsigned. Trusted-publisher signing and GitHub Release publication
  are not part of this local build.
- Full-suite scientific hard audits and dependency source-redistribution review
  remain separate from this development packaging check.

Raw installer logs remain in ignored local storage because they contain machine
paths. No installation is left registered by the completed lifecycle tests.

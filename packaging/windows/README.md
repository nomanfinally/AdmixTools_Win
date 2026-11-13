# Native Windows distribution

The builder produces a branded, traditional Windows Installer wizard with
license, destination selection, an optional **user PATH** checkbox, installation
progress, repair and uninstall. The compressed cabinet and all native runtime
dependencies are embedded in the MSI. Installation is per user; machine PATH
and scientific command output are unchanged.

The MSI and portable ZIP contain 37 supported native executables, Graphviz,
Ghostscript, their non-system DLL dependencies, rendering resources, notices
and documentation. Optional interpreter scripts and the blocked `qpfmvmix`
target are excluded. No Python, MSYS2, WSL, compiler or network is required to
run the installed native commands. This does not certify full-suite Linux parity.

## Build

Use native x64 Windows and the source prerequisites from
[README.WINDOWS.md](../../README.WINDOWS.md). Install the rendering dependencies
in the same MSYS2 **UCRT64** environment as the scientific libraries:

```sh
pacman -S --needed mingw-w64-ucrt-x86_64-graphviz mingw-w64-ucrt-x86_64-ghostscript
```

Then use PowerShell in the checkout:

```powershell
.\build-installer-windows.ps1 -Rebuild -Msys2Root 'C:\msys64' -Version '8.1.0'
```

The first packaging run downloads a checksum-pinned WiX 6.0.2 CLI and its UI
extension. Build tools are extracted into the ignored local packaging cache;
they are not registered as a system installation or shipped to users. Review
the [WiX tooling terms](https://docs.firegiant.com/wix/) when using these tools.
An existing matching WiX CLI can be supplied with `-WixPath`.

Without `-Rebuild`, the builder packages the existing `bin` only after checking
the complete supported executable inventory, native source hashes, runtime
hashes and x64 architecture. It rejects stale source/build metadata. The
renderer DLL closure is resolved from the selected UCRT64 tree. Required
upstream/dependency notices are retained under `docs` and `bin\licenses`.
For publication, also collect the matching source bundle described below.
It preserves the project, patched argp sources and MSYS2 dependency source
packages, including their upstream sources and build recipes.

Outputs in ignored `dist`:

- `AdmixTools-<version>-windows-x64.msi`: single-file offline installer.
- The matching `.zip`: portable native payload.
- `.manifest.json`: sanitized provenance and every installed payload hash.
- `.sha256`: artifact checksums.

Existing output names are never overwritten. Use `-OutputDirectory` for another
build destination or increase `-Version` for a new distributed build. The
three-part numeric MSI version is independent of the executable `.w` strings.
The builder neither signs artifacts nor commits, uploads or creates releases.
No private guide, raw audit log or WiX debug-symbol database is packaged.

## Validate

See [recorded development results and remaining checks](VALIDATION.md) for the
14 November 2026 artifact. Do not substitute packaging success for scientific
compatibility validation.

Use an isolated Windows test account without an existing MSI installation:

```powershell
.\tests\windows\test_installer_windows.ps1 `
    -MsiPath '.\dist\AdmixTools-8.1.0-windows-x64.msi'
```

The test temporarily installs into paths containing spaces, checks every file
against the manifest, exercises both PATH choices, runs commands with a minimal
PATH, repairs a deliberately damaged executable, uninstalls, and checks that
unrelated PATH values and a user-created file survive. Raw logs are ignored and
may contain machine paths. Reboots and Restart Manager application shutdown are
explicitly disabled in the test and in the package.

WiX validates the MSI during compilation. Wizard artwork is generated from
repository-owned drawing code in `branding.ps1`; the standard WiX dialog layout
supplies keyboard navigation and maintenance pages. A desktop walkthrough and
testing on a separate clean Windows machine remain necessary before treating a
development artifact as a broadly validated release. Installed software is
unsigned until a maintainer adds a trusted code-signing certificate.

## Rebuild after code changes

Commit the intended source changes on `main`, then rebuild all supported native
tools and the installer. Increase the three-part installer version for every
distributed update, even when upstream executable version codes have not changed.
For example, after distributing installer version `8.1.0`:

```powershell
.\build-installer-windows.ps1 -Rebuild -Msys2Root 'C:\msys64' -Version '8.1.1'
.\tests\windows\test_installer_windows.ps1 -MsiPath '.\dist\AdmixTools-8.1.1-windows-x64.msi'
python .\packaging\windows\collect_sources.py `
    --manifest '.\dist\AdmixTools-8.1.1-windows-x64.manifest.json' `
    --runtime-root 'C:\msys64\ucrt64'
```

Repeat applicable pristine Linux comparisons after code changes and record their
actual results before distributing the new build. Installer lifecycle success
does not replace scientific parity checks. A local rebuild does not update a
previously downloaded installer or publish anything automatically.

The source collector requires a clean tracked working tree. It checks packaged
runtime hashes against the selected MSYS2 installation, identifies exact package
versions, downloads matching source archives into an ignored cache, and creates
`AdmixTools-<version>-windows-x64-sources.zip` plus its checksum. It includes the
tracked project tree and the actual pinned/patched argument-parser sources;
private guides and local logs are not tracked and are excluded. Run it on the
original build machine before updating dependencies. Source collection needs
internet access; recipients installing the MSI do not.

## Publish a downloadable GitHub release

Use **Releases > Draft a new release** on
[the fork](https://github.com/nomanfinally/AdmixTools_Win/releases). Select a new
tag targeting the exact source commit. Upload the MSI, portable ZIP, sanitized
manifest, checksums, matching sources and validation notes as release assets.
Keep binaries in Releases; `dist` remains ignored by Git. Publish development
builds as **pre-releases**, with the unsigned status and remaining validation
clearly stated. Keep existing tags/assets intact and create a new release for
each update instead of overwriting an old installer.

The first development package uses tag `v8.1.0.w-preview.1` and numeric MSI
version `8.1.0`. Future tags can track their package version, for example
`v8.1.1.w-preview.2`. These tags and MSI versions do not replace each executable's
upstream version plus `.w`.

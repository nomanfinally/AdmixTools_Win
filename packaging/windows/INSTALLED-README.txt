ADMIXTOOLS Windows - development build

The bin directory contains the native x64 executables and required DLLs. Keep
them together. If you selected the PATH option, open a new PowerShell window
and run qpAdm -h. Otherwise invoke bin\qpAdm.exe using its complete path.

Run analyses from a separate working directory containing your parameter and
population files. Keep datasets and results outside this installation folder.
Save ordinary results through stdout redirection or Tee-Object as described in
docs\README.WINDOWS.md. This is a command-line suite, not a graphical analysis app.

The MSI installs for your Windows account. It supports repair and uninstall via
Windows Settings > Apps. Uninstall removes the installer-managed PATH entry and
installed files; user-created files are not recursively removed. Close running
AdmixTools programs before repair, upgrade or uninstall.

Graphviz and Ghostscript are bundled for native graph rendering. Native analyses
and rendering require neither MSYS2, a compiler, WSL, Python nor internet access.
The optional interpreter-based workflows remain in the source repository and
are not installed by this native-only package.

The package retains upstream calculations and known upstream defects. Packaging
is not certification of every tool's numerical parity. See the public repository
for the precise recorded compatibility scope, source, and development status:
https://github.com/nomanfinally/AdmixTools_Win

Upstream source: https://github.com/DReichLab/AdmixTools
Upstream and dependency license notices are in docs and bin\licenses.

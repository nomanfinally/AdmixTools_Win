[CmdletBinding()]
param(
    [string]$SourceRoot = '',
    [string]$InstallRoot = '',
    [string]$Msys2Root = '',
    [ValidateSet('Machine', 'User', 'None')][string]$PathScope = 'Machine',
    [switch]$CheckOnly,
    [switch]$NoInstallDependencies
)
$ErrorActionPreference = 'Stop'

function Invoke-SetupCommand {
    param([string]$Program, [string[]]$Arguments)
    # In Windows PowerShell, redirected native stderr can become an ErrorRecord.
    # Display diagnostics but decide success from the native exit code.
    $taskNativePreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Program @Arguments 2>&1 | ForEach-Object {
            if ($_ -is [Management.Automation.ErrorRecord]) { Write-Host $_.Exception.Message }
            else { Write-Host $_ }
        }
        $taskNativeExit = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $taskNativePreference }
    if ($taskNativeExit -ne 0) { throw "$Program failed with exit code $taskNativeExit." }
}

function Get-SetupExecutable {
    param([string]$Name)
    $taskCommand = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($taskCommand) { return $taskCommand.Source }
    return $null
}

function Refresh-SetupPath {
    # Retain caller-specific entries while discovering newly installed commands.
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
        [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:Path
}

function Get-SetupPython {
    $taskPython = Get-SetupExecutable 'python.exe'
    if (-not $taskPython) { return $null }
    $taskProbePreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $taskPython -c "import sys, struct, venv, ensurepip; sys.exit(0 if sys.version_info >= (3,10) and struct.calcsize('P') == 8 else 1)" *> $null }
    finally { $ErrorActionPreference = $taskProbePreference }
    if ($LASTEXITCODE -eq 0) { return $taskPython }
    return $null
}

function Install-SetupPrerequisite {
    param([string]$Id, [string[]]$Extra = @())
    $taskWinget = Get-SetupExecutable 'winget.exe'
    if (-not $taskWinget) {
        throw "Missing $Id and WinGet is unavailable. Install prerequisites using README.WINDOWS.md, then retry."
    }
    Write-Host "Installing required prerequisite: $Id"
    & $taskWinget install --id $Id --exact --source winget --silent --accept-package-agreements --accept-source-agreements @Extra
    if ($LASTEXITCODE -notin @(0, 3010)) { throw "WinGet could not install $Id (exit $LASTEXITCODE)." }
    Refresh-SetupPath
}

function Find-SetupMsys {
    param([string]$Requested)
    if ($Requested) { return [IO.Path]::GetFullPath($Requested) }
    $taskCandidates = @($env:MSYS2_ROOT, 'C:\msys64')
    if ($env:LOCALAPPDATA) { $taskCandidates += Join-Path $env:LOCALAPPDATA 'AdmixTools-build\msys64' }
    $taskGcc = Get-SetupExecutable 'gcc.exe'
    if ($taskGcc -and $taskGcc -match '[\\/]ucrt64[\\/]bin[\\/]gcc\.exe$') {
        $taskCandidates += Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $taskGcc))
    }
    foreach ($taskCandidate in $taskCandidates) {
        if ($taskCandidate -and (Test-Path -LiteralPath (Join-Path $taskCandidate 'usr\bin\pacman.exe') -PathType Leaf)) {
            return [IO.Path]::GetFullPath($taskCandidate)
        }
    }
    return 'C:\msys64'
}

function Get-SetupMissingPackages {
    param([string]$MsysRoot)
    $taskPacman = Join-Path $MsysRoot 'usr\bin\pacman.exe'
    $taskPackages = @('mingw-w64-ucrt-x86_64-gcc', 'mingw-w64-ucrt-x86_64-binutils',
        'mingw-w64-ucrt-x86_64-gsl', 'mingw-w64-ucrt-x86_64-openblas', 'mingw-w64-ucrt-x86_64-zlib')
    foreach ($taskPackage in $taskPackages) {
        if (-not (Test-Path -LiteralPath $taskPacman -PathType Leaf)) { $taskPackage; continue }
        $taskQueryPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try { & $taskPacman -Q $taskPackage *> $null }
        finally { $ErrorActionPreference = $taskQueryPreference }
        if ($LASTEXITCODE -ne 0) { $taskPackage }
    }
}

function Get-SetupPathValue {
    param([AllowEmptyString()][string]$Existing, [string]$BinDirectory)
    $taskCompare = $BinDirectory.TrimEnd('\', '/')
    $taskOthers = @($Existing -split ';' | Where-Object {
        $_ -and [Environment]::ExpandEnvironmentVariables($_.Trim().Trim('"')).TrimEnd('\', '/') -ine $taskCompare
    })
    return (@($BinDirectory) + $taskOthers) -join ';'
}

function Send-SetupEnvironmentChange {
    if (-not ('AdmixToolsSetup.EnvironmentNotice' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace AdmixToolsSetup {
 public static class EnvironmentNotice {
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern IntPtr SendMessageTimeout(IntPtr window, uint message,
    UIntPtr wparam, string lparam, uint flags, uint timeout, out UIntPtr result);
 }
}
'@
    }
    $taskNoticeResult = [UIntPtr]::Zero
    [void][AdmixToolsSetup.EnvironmentNotice]::SendMessageTimeout([IntPtr]0xffff, 0x001A,
        [UIntPtr]::Zero, 'Environment', 2, 5000, [ref]$taskNoticeResult)
}

function Assert-SetupMove {
    param([string]$Path, [string]$Parent, [string[]]$Allowed)
    $taskFull = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ($taskFull -notin $Allowed -or (Split-Path -Parent $taskFull) -ine $Parent) {
        throw 'Refusing a move outside the explicitly selected installation locations.'
    }
    if (Test-Path -LiteralPath $taskFull) {
        $taskItem = Get-Item -LiteralPath $taskFull -Force
        if ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'Installation/build destinations must not be junctions or symbolic links.'
        }
    }
    $taskAncestor = Split-Path -Parent $taskFull
    while ($taskAncestor) {
        if ((Test-Path -LiteralPath $taskAncestor) -and
            ((Get-Item -LiteralPath $taskAncestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Installation ancestors must not redirect through junctions or symbolic links.'
        }
        $taskNextAncestor = Split-Path -Parent $taskAncestor
        if ($taskNextAncestor -eq $taskAncestor) { break }
        $taskAncestor = $taskNextAncestor
    }
}

function Move-SetupDirectory {
    param([string]$From, [string]$To, [string]$Parent, [string[]]$Allowed)
    for ($taskAttempt = 0; $taskAttempt -lt 6; $taskAttempt++) {
        Assert-SetupMove $From $Parent $Allowed
        Assert-SetupMove $To $Parent $Allowed
        if (Test-Path -LiteralPath $To) { throw "Refusing to merge an installation into an existing destination: $To" }
        try { Move-Item -LiteralPath $From -Destination $To -ErrorAction Stop; return }
        catch [IO.IOException] {
            if ($taskAttempt -eq 5) { throw }
            Start-Sleep -Milliseconds 500
        }
    }
}

function Invoke-AdmixToolsSetup {
    param([string]$SourceRoot, [string]$InstallRoot, [string]$Msys2Root,
        [string]$PathScope = 'Machine', [switch]$CheckOnly, [switch]$NoInstallDependencies)
    if (-not [Environment]::Is64BitOperatingSystem -or -not [Environment]::Is64BitProcess) {
        throw 'Use 64-bit Windows and 64-bit PowerShell for this x64 build.'
    }
    $taskSource = (Resolve-Path -LiteralPath $SourceRoot).Path.TrimEnd('\')
    if (-not (Test-Path -LiteralPath (Join-Path $taskSource 'src\build_windows.py'))) {
        throw 'SourceRoot must name the AdmixTools Windows source checkout.'
    }
    if (-not $InstallRoot) {
        $taskPrograms = if ($env:ProgramW6432) { $env:ProgramW6432 } else { $env:ProgramFiles }
        $InstallRoot = Join-Path $taskPrograms 'AdmixTools'
    }
    $taskInstall = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
    if ($taskInstall -notmatch '^[A-Za-z]:\\' -or
        $taskInstall.TrimEnd('\') -ieq [IO.Path]::GetPathRoot($taskInstall).TrimEnd('\') -or
        $taskInstall -ieq $taskSource -or $taskSource.StartsWith($taskInstall + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $taskInstall.StartsWith($taskSource + '\src\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Select a dedicated local installation folder, separate from the source checkout and its src directory.'
    }
    if ($taskInstall.StartsWith($taskSource + '\', [StringComparison]::OrdinalIgnoreCase)) {
        $taskRelativeInstall = $taskInstall.Substring($taskSource.Length + 1).Replace('\', '/') + '/'
        & git -C $taskSource check-ignore --quiet -- $taskRelativeInstall
        if ($LASTEXITCODE -ne 0) { throw 'An installation inside the checkout must be ignored by Git to keep generated files and local paths private.' }
    }
    $taskParent = Split-Path -Parent $taskInstall
    $taskAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
    $taskProtected = @($env:ProgramFiles, $env:ProgramW6432, ${env:ProgramFiles(x86)}, $env:SystemRoot) |
        Where-Object { $_ -and ($taskInstall -ieq $_ -or $taskInstall.StartsWith($_.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) }
    if (-not $CheckOnly -and -not $taskAdmin -and ($PathScope -eq 'Machine' -or $taskProtected)) {
        throw 'Program Files installation and machine PATH changes require elevation. Right-click build-install-windows.bat and choose Run as administrator. Use -CheckOnly for a read-only check.'
    }
    $taskMsys = Find-SetupMsys $Msys2Root
    $taskGit = Get-SetupExecutable 'git.exe'
    $taskPython = Get-SetupPython
    $taskMissing = @(Get-SetupMissingPackages $taskMsys)
    Write-Host "Install folder: $taskInstall"
    Write-Host "MSYS2 root: $taskMsys"
    Write-Host "PATH scope: $PathScope"
    if ($CheckOnly) {
        Write-Host "Git available: $([bool]$taskGit)"
        Write-Host "Native x64 Python >= 3.10 with venv/pip: $([bool]$taskPython)"
        Write-Host "Missing UCRT64 packages: $($taskMissing -join ', ')"
        if (-not $taskGit -or -not $taskPython -or $taskMissing.Count) { throw 'Prerequisite check failed. See missing requirements above.' }
        Write-Host 'Prerequisites found. No packages, installation files or PATH settings were changed.'
        return
    }
    if ((-not $taskGit -or -not $taskPython -or $taskMissing.Count) -and $NoInstallDependencies) {
        throw 'Required prerequisites are missing; -NoInstallDependencies prevents WinGet/pacman changes. See README.WINDOWS.md.'
    }
    if (-not $taskGit) { Install-SetupPrerequisite 'Git.Git'; $taskGit = Get-SetupExecutable 'git.exe' }
    if (-not $taskPython) { Install-SetupPrerequisite 'Python.Python.3.13' @('--architecture', 'x64'); $taskPython = Get-SetupPython }
    if (-not $taskGit -or -not $taskPython) { throw 'Git or native Python is still unavailable after prerequisite installation. Reopen an administrator terminal and retry.' }
    if (-not (Test-Path -LiteralPath (Join-Path $taskMsys 'usr\bin\bash.exe'))) {
        Install-SetupPrerequisite 'MSYS2.MSYS2' @('--location', $taskMsys)
    }
    if (@(Get-SetupMissingPackages $taskMsys).Count) {
        $taskBash = Join-Path $taskMsys 'usr\bin\bash.exe'
        # Separate full-upgrade processes handle an MSYS2 core runtime update.
        Invoke-SetupCommand $taskBash @('-lc', 'pacman --noconfirm -Syuu')
        Invoke-SetupCommand $taskBash @('-lc', 'pacman --noconfirm -Syuu')
        Invoke-SetupCommand $taskBash @('-lc', 'pacman --noconfirm -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-binutils mingw-w64-ucrt-x86_64-gsl mingw-w64-ucrt-x86_64-openblas mingw-w64-ucrt-x86_64-zlib')
    }
    if (@(Get-SetupMissingPackages $taskMsys).Count) { throw 'Required UCRT64 packages are still missing.' }
    foreach ($taskName in 'gcc.exe', 'ar.exe', 'objdump.exe', 'windres.exe') {
        if (-not (Test-Path -LiteralPath (Join-Path $taskMsys "ucrt64\bin\$taskName"))) { throw "Missing tool: $taskName" }
    }
    $taskRevision = & $taskGit -C $taskSource rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Use a Git source checkout so build provenance can be recorded.' }
    $taskDirty = [bool](& $taskGit -C $taskSource status --porcelain -- src perlsrc build-windows.ps1 prepare-windows.ps1)
    $taskMarkerName = 'admixtools-install.json'
    $taskExistingRecordHash = $null
    if (Test-Path -LiteralPath $taskInstall) {
        $taskMarker = Join-Path $taskInstall $taskMarkerName
        if (-not (Test-Path -LiteralPath $taskMarker)) {
            throw 'The destination already exists without an AdmixTools installation record. Select an empty new location; existing files will not be overwritten.'
        }
        $taskPreviousRecord = Get-Content -LiteralPath $taskMarker -Raw | ConvertFrom-Json
        if ($taskPreviousRecord.product -ne 'AdmixTools Windows') {
            throw 'The destination does not contain a recognized AdmixTools installation.'
        }
        if ($taskPreviousRecord.path_scope -ne $PathScope) {
            throw 'Keep the existing PATH scope when updating this installation, or remove its old PATH entry explicitly before changing scopes.'
        }
        $taskExistingRecordHash = (Get-FileHash -LiteralPath $taskMarker -Algorithm SHA256).Hash
    }
    New-Item -ItemType Directory -Path $taskParent -Force | Out-Null
    $taskId = [Guid]::NewGuid().ToString('N')
    $taskStage = Join-Path $taskParent ('.AdmixTools-build-' + $taskId)
    $taskBackup = Join-Path $taskParent ((Split-Path -Leaf $taskInstall) + '.backup-' + $taskId)
    $taskAllowed = @($taskInstall, $taskStage, $taskBackup)
    $taskBuildSource = Join-Path $taskStage 'source'
    $taskPromoted = $false
    $taskPreviousMoved = $false
    $taskPathChanged = $false
    $taskOldPath = if ($PathScope -ne 'None') { [Environment]::GetEnvironmentVariable('Path', $PathScope) } else { $null }
    $taskTranscript = Join-Path $env:TEMP ('AdmixTools-build-install-' + $taskId + '.log')
    Start-Transcript -Path $taskTranscript | Out-Null
    try {
        New-Item -ItemType Directory -Path $taskBuildSource -ErrorAction Stop | Out-Null
        Write-Host "Local setup log: $taskTranscript"
        Write-Host 'Copying current tracked source into the installation build area...'
        $taskFiles = & $taskGit -C $taskSource ls-files -- src perlsrc build-windows.ps1 prepare-windows.ps1 UPSTREAM_BASELINE README README.INSTALL README.WINDOWS.md README.3PopTest README.CONVERTF README.Dstatistics README.F4RatioTest README.qpfstats README.qpWave README.QPGRAPH README.qp4diff README.ROLLOFF README.ROLLOFF_OUTPUT tests/windows/parity.py
        if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate tracked source files.' }
        foreach ($taskRelative in $taskFiles) {
            $taskDestination = Join-Path $taskBuildSource $taskRelative
            New-Item -ItemType Directory -Path (Split-Path -Parent $taskDestination) -Force | Out-Null
            Copy-Item -LiteralPath (Join-Path $taskSource $taskRelative) -Destination $taskDestination -ErrorAction Stop
        }
        $taskPowerShell = Join-Path $PSHOME 'powershell.exe'
        if (-not (Test-Path -LiteralPath $taskPowerShell)) { $taskPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe' }
        Write-Host 'Preparing pinned GNU argp and its private build environment...'
        Invoke-SetupCommand $taskPowerShell @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            (Join-Path $taskBuildSource 'prepare-windows.ps1'), '-Msys2Root', $taskMsys)
        $taskBuildArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $taskBuildSource 'build-windows.ps1'),
            '-Msys2Root', $taskMsys, '-SourceRevision', $taskRevision)
        if ($taskDirty) { $taskBuildArgs += '-SourceDirty' }
        Write-Host 'Compiling the supported native suite...'
        Invoke-SetupCommand $taskPowerShell $taskBuildArgs
        $taskBuiltBin = Join-Path $taskBuildSource 'bin'
        $taskBuildInfo = Get-Content -LiteralPath (Join-Path $taskBuiltBin 'windows-build.json') -Raw | ConvertFrom-Json
        foreach ($taskTool in $taskBuildInfo.executables) {
            if (-not (Test-Path -LiteralPath (Join-Path $taskBuiltBin ($taskTool + '.exe')))) { throw "Missing built executable: $taskTool" }
        }
        foreach ($taskDll in $taskBuildInfo.runtime_sha256.PSObject.Properties) {
            if ((Get-FileHash -LiteralPath (Join-Path $taskBuiltBin $taskDll.Name) -Algorithm SHA256).Hash -ine $taskDll.Value) {
                throw "Runtime dependency verification failed: $($taskDll.Name)"
            }
        }
        Write-Host 'Running synthetic integration checks...'
        $taskValidation = Join-Path $taskStage 'validation'
        Invoke-SetupCommand $taskPython @((Join-Path $taskBuildSource 'tests\windows\parity.py'), '--bin', $taskBuiltBin, '--output', $taskValidation)
        $taskResults = Get-Content -LiteralPath (Join-Path $taskValidation 'manifest.json') -Raw | ConvertFrom-Json
        foreach ($taskCase in $taskResults.cases.PSObject.Properties) {
            $taskExpected = if ($taskCase.Name -eq 'transpose-invalid') { 64 } else { 0 }
            if ($null -eq $taskCase.Value.returncode -or $taskCase.Value.returncode -ne $taskExpected) { throw "Integration check failed: $($taskCase.Name)" }
        }
        if (-not $taskResults.binary_roundtrip_exact) { throw 'Binary genotype round trip failed.' }
        Copy-Item -LiteralPath $taskBuiltBin -Destination (Join-Path $taskStage 'bin') -Recurse -ErrorAction Stop
        $taskFinalBin = Join-Path $taskInstall 'bin'
        $taskRecord = [ordered]@{ schema = 1; product = 'AdmixTools Windows'; source_revision = $taskRevision;
            source_snapshot_dirty = $taskDirty; upstream_commit = $taskBuildInfo.upstream_commit;
            built_utc = [DateTime]::UtcNow.ToString('o'); executables = $taskBuildInfo.executables;
            path_scope = $PathScope; previous_path = $taskOldPath; path_entry = $taskFinalBin;
            synthetic_cases = @($taskResults.cases.PSObject.Properties).Count; linux_parity_certified = $false }
        [IO.File]::WriteAllText((Join-Path $taskStage $taskMarkerName), ($taskRecord | ConvertTo-Json -Depth 6), (New-Object Text.UTF8Encoding $false))
        foreach ($taskPath in $taskAllowed) { Assert-SetupMove $taskPath $taskParent $taskAllowed }
        if (Test-Path -LiteralPath $taskInstall) {
            $taskCurrentMarker = Join-Path $taskInstall $taskMarkerName
            if (-not $taskExistingRecordHash -or -not (Test-Path -LiteralPath $taskCurrentMarker) -or
                (Get-FileHash -LiteralPath $taskCurrentMarker -Algorithm SHA256).Hash -ne $taskExistingRecordHash) {
                throw 'The installation destination changed during the build. It has been left untouched; retry after reviewing it.'
            }
            Move-SetupDirectory $taskInstall $taskBackup $taskParent $taskAllowed
            $taskPreviousMoved = $true
        }
        Move-SetupDirectory $taskStage $taskInstall $taskParent $taskAllowed
        $taskPromoted = $true
        if ($PathScope -ne 'None') {
            # Re-read after compilation so concurrent unrelated PATH changes
            # are preserved, rather than overwriting an earlier snapshot.
            $taskOldPath = [Environment]::GetEnvironmentVariable('Path', $PathScope)
            $taskRecord.previous_path = $taskOldPath
            [IO.File]::WriteAllText((Join-Path $taskInstall $taskMarkerName), ($taskRecord | ConvertTo-Json -Depth 6), (New-Object Text.UTF8Encoding $false))
            $taskNewPath = Get-SetupPathValue ([string]$taskOldPath) $taskFinalBin
            [Environment]::SetEnvironmentVariable('Path', $taskNewPath, $PathScope)
            $taskPathChanged = $true
            Send-SetupEnvironmentChange
        }
        Invoke-SetupCommand (Join-Path $taskFinalBin 'qpAdm.exe') @('-h')
        Write-Host "Installed $($taskBuildInfo.executables.Count) native tools in $taskFinalBin"
        if ($taskPreviousMoved) { Write-Host "Previous installation retained: $taskBackup" }
        Write-Host 'Open a new PowerShell window to use the updated PATH. Reopen VS Code if needed.'
        Write-Host 'These are functional checks, not certification of full Linux numerical parity.'
    }
    catch {
        $taskOriginalFailure = $_
        Write-Host "Setup failed: $($taskOriginalFailure.Exception.Message)"
        try {
            if ($taskPathChanged) { [Environment]::SetEnvironmentVariable('Path', $taskOldPath, $PathScope) }
            if ($taskPromoted) { Move-SetupDirectory $taskInstall $taskStage $taskParent $taskAllowed }
            if ($taskPreviousMoved) { Move-SetupDirectory $taskBackup $taskInstall $taskParent $taskAllowed }
        }
        catch {
            Write-Host "Rollback also needs attention: $($_.Exception.Message)"
            Write-Host "Previous installation backup (if moved): $taskBackup"
        }
        Write-Host "Failed build files retained for diagnosis: $taskStage"
        throw $taskOriginalFailure
    }
    finally { Stop-Transcript | Out-Null }
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        if (-not $SourceRoot) { $SourceRoot = $PSScriptRoot }
        Invoke-AdmixToolsSetup -SourceRoot $SourceRoot -InstallRoot $InstallRoot -Msys2Root $Msys2Root -PathScope $PathScope -CheckOnly:$CheckOnly -NoInstallDependencies:$NoInstallDependencies
        exit 0
    }
    catch { Write-Error $_ -ErrorAction Continue; exit 1 }
}

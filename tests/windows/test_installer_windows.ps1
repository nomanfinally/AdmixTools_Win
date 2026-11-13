[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$MsiPath,
    [string]$OutputDirectory = ''
)
$ErrorActionPreference = 'Stop'
$taskMsi = (Resolve-Path -LiteralPath $MsiPath).Path
# Refuse unrelated packages, and verify authored restart protection before
# running any installer transaction on the test account.
$taskInstaller = New-Object -ComObject WindowsInstaller.Installer
$taskDatabase = $taskInstaller.OpenDatabase($taskMsi, 0)
$taskPropertyView = $taskDatabase.OpenView('SELECT `Property`, `Value` FROM `Property`')
$taskPropertyView.Execute()
$taskProperties = @{}
while ($taskRow = $taskPropertyView.Fetch()) {
    $taskProperties[$taskRow.StringData(1)] = $taskRow.StringData(2)
}
$taskPropertyView.Close()
if ($taskProperties.ProductName -ne 'AdmixTools Windows' -or
    $taskProperties.UpgradeCode -ine '{75FD6BD3-47A1-45DF-A0BA-E9ED4B5B701E}' -or
    $taskProperties.REBOOT -ne 'ReallySuppress' -or
    $taskProperties.MSIRESTARTMANAGERCONTROL -ne 'Disable') {
    throw 'Not the expected AdmixTools package with authored restart protection.'
}
[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskPropertyView)
[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDatabase)
[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskInstaller)
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $PSScriptRoot ("..\..\validation-results\installer-" + [Guid]::NewGuid().ToString('N'))
}
$taskOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDirectory)
New-Item -ItemType Directory -Path $taskOutput -ErrorAction Stop | Out-Null
if (Test-Path 'HKCU:\Software\AdmixToolsWindows') {
    throw 'An existing AdmixTools MSI registration is present. Use an isolated Windows test account.'
}
$taskUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$taskMachinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
$taskOldProcessPath = $env:Path
$taskResults = [ordered]@{ architecture = 'x64'; cases = @(); passed = $false }
$taskInstalled = $false

function Invoke-TestMsi {
    param([string[]]$Arguments, [string]$LogName)
    $taskLog = Join-Path $taskOutput $LogName
    $taskProcess = Start-Process -FilePath msiexec.exe -WindowStyle Hidden -PassThru -Wait -ArgumentList (
        $Arguments + @('REBOOT=ReallySuppress', 'MSIRESTARTMANAGERCONTROL=Disable', '/qn', '/norestart', '/l*v', ('"' + $taskLog + '"')))
    if ($taskProcess.ExitCode -notin @(0, 3010)) {
        throw "MSI operation failed with exit $($taskProcess.ExitCode); see $taskLog"
    }
}

function Invoke-TestNative {
    param([string]$Executable, [string[]]$Arguments, [string]$LogName)
    $taskPreviousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Executable @Arguments *> (Join-Path $taskOutput $LogName)
        $taskNativeExit = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $taskPreviousPreference }
    if ($taskNativeExit -ne 0) { throw "Installed native command failed: $LogName (exit $taskNativeExit)" }
}

try {
    foreach ($taskChoice in @('0', '1')) {
        $taskInstall = Join-Path $taskOutput ("Install with spaces " + $taskChoice)
        Invoke-TestMsi @('/i', ('"' + $taskMsi + '"'), ('INSTALLFOLDER="' + $taskInstall + '"'),
            ('ADDTOPATH=' + $taskChoice)) ("install-" + $taskChoice + '.log')
        $taskInstalled = $true
        $taskManifestPath = [IO.Path]::ChangeExtension($taskMsi, '.manifest.json')
        $taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json
        foreach ($taskFile in $taskManifest.payload_sha256.PSObject.Properties) {
            $taskInstalledFile = Join-Path $taskInstall $taskFile.Name
            if ((Get-FileHash -LiteralPath $taskInstalledFile -Algorithm SHA256).Hash -ine $taskFile.Value) {
                throw "Installed byte mismatch: $($taskFile.Name)"
            }
        }
        $taskBin = Join-Path $taskInstall 'bin'
        $taskEnvPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        $taskEntries = @($taskEnvPath -split ';' | Where-Object { $_.TrimEnd('\') -ieq $taskBin.TrimEnd('\') })
        if (($taskChoice -eq '1' -and $taskEntries.Count -ne 1) -or ($taskChoice -eq '0' -and $taskEntries.Count -ne 0)) {
            throw 'PATH checkbox behavior differs from requested choice.'
        }
        # A clean process PATH prevents accidentally using MSYS2 or another port.
        $env:Path = $taskBin + ';' + (Join-Path $env:SystemRoot 'System32')
        Invoke-TestNative (Join-Path $taskBin 'qpAdm.exe') @('-h') ('help-' + $taskChoice + '.txt')
        Invoke-TestNative (Join-Path $taskBin 'dot.exe') @('-V') ('dot-' + $taskChoice + '.txt')
        Invoke-TestNative (Join-Path $taskBin 'gswin64c.exe') @('--version') ('gs-' + $taskChoice + '.txt')
        $taskDot = Join-Path $taskOutput ('render-' + $taskChoice + '.dot')
        $taskPs = [IO.Path]::ChangeExtension($taskDot, '.ps')
        $taskPdf = [IO.Path]::ChangeExtension($taskDot, '.pdf')
        [IO.File]::WriteAllText($taskDot, 'digraph G { A [label="Native Windows"]; A -> B; }')
        Invoke-TestNative (Join-Path $taskBin 'dot.exe') @('-Tps', $taskDot, '-o', $taskPs) ('render-dot-' + $taskChoice + '.txt')
        Invoke-TestNative (Join-Path $taskBin 'gswin64c.exe') @('-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=pdfwrite',
            ('-sOutputFile=' + $taskPdf), $taskPs) ('render-pdf-' + $taskChoice + '.txt')
        if (-not (Test-Path -LiteralPath $taskPdf) -or (Get-Item -LiteralPath $taskPdf).Length -lt 100) {
            throw 'Bundled rendering did not produce a PDF.'
        }
        # Exercise the native analysis-to-renderer call with PATH unchecked:
        # helpers must be found beside the installed executable.
        $taskGraph = Join-Path $taskOutput ('graph-' + $taskChoice + '.txt')
        $taskToolDot = Join-Path $taskOutput ('tool-render-' + $taskChoice + '.dot')
        $taskToolPdf = [IO.Path]::ChangeExtension($taskToolDot, '.pdf')
        [IO.File]::WriteAllLines($taskGraph, @('root R', 'label Out O', 'label A A', 'label B B',
            'label C C', 'label X X', 'edge o R O', 'edge q R Q', 'edge ab Q AB',
            'edge a AB A', 'edge b AB B', 'edge c Q C', 'admix XX AB C 60 40', 'edge x XX X'))
        $env:Path = Join-Path $env:SystemRoot 'System32'
        Push-Location -LiteralPath $taskOutput
        try {
            Invoke-TestNative (Join-Path $taskBin 'qpreroot.exe') @('-g', $taskGraph, '-d', $taskToolDot) ('tool-render-' + $taskChoice + '.txt')
        }
        finally { Pop-Location }
        if (-not (Test-Path -LiteralPath $taskToolPdf) -or (Get-Item -LiteralPath $taskToolPdf).Length -lt 100) {
            throw 'Installed qpreroot did not find its bundled rendering helpers without PATH.'
        }
        $env:Path = $taskOldProcessPath
        $taskSentinel = Join-Path $taskInstall 'user-created-file.txt'
        [IO.File]::WriteAllText($taskSentinel, 'preserve user data')
        $taskRepairFile = Join-Path $taskBin 'qpAdm.exe'
        # A deliberately damaged installed file exercises forced-file repair.
        [IO.File]::WriteAllText($taskRepairFile, 'repair probe')
        Invoke-TestMsi @('/i', ('"' + $taskMsi + '"'), 'REINSTALL=ALL', 'REINSTALLMODE=amus') ('repair-' + $taskChoice + '.log')
        if ((Get-FileHash -LiteralPath $taskRepairFile -Algorithm SHA256).Hash -ine $taskManifest.payload_sha256.'bin/qpAdm.exe') {
            throw 'Repair did not restore the native executable.'
        }
        $taskAfterRepair = [Environment]::GetEnvironmentVariable('Path', 'User')
        if (@($taskAfterRepair -split ';' | Where-Object { $_.TrimEnd('\') -ieq $taskBin.TrimEnd('\') }).Count -ne $taskEntries.Count) {
            throw 'Repair duplicated or unexpectedly added PATH.'
        }
        Invoke-TestMsi @('/x', ('"' + $taskMsi + '"')) ('uninstall-' + $taskChoice + '.log')
        $taskInstalled = $false
        if (Test-Path -LiteralPath $taskRepairFile) { throw 'Uninstall left an installed executable.' }
        if ([IO.File]::ReadAllText($taskSentinel) -ne 'preserve user data') { throw 'Uninstall removed user data.' }
        if ([Environment]::GetEnvironmentVariable('Path', 'User') -cne $taskUserPath) { throw 'Uninstall did not restore user PATH.' }
        if ([Environment]::GetEnvironmentVariable('Path', 'Machine') -cne $taskMachinePath) { throw 'Machine PATH changed.' }
        $taskResults.cases += [ordered]@{ add_to_path = $taskChoice; installed_file_hashes = 'exact'; repair = 'passed';
            uninstall = 'passed'; preserved_user_file = $true; path_restored = $true; ps_pdf_rendering = 'passed';
            sibling_renderers_without_path = 'passed' }
    }
    $taskResults.passed = $true
}
finally {
    $env:Path = $taskOldProcessPath
    if ($taskInstalled) {
        try { Invoke-TestMsi @('/x', ('"' + $taskMsi + '"')) 'cleanup-uninstall.log' } catch { Write-Warning $_ }
    }
    [IO.File]::WriteAllText((Join-Path $taskOutput 'verification.json'), ($taskResults | ConvertTo-Json -Depth 8),
        (New-Object Text.UTF8Encoding $false))
}
Write-Output 'Installer lifecycle checks passed for PATH off and on; user data and existing PATH preserved.'

<# Integration-boundary tests using an already successfully built payload.
   Child commands are injected for failure tests; no system packages or PATH
   values are installed/changed. All filesystem tests stay in ignored output. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$BuiltInstallRoot,
    [Parameter(Mandatory = $true)][string]$Msys2Root,
    [Parameter(Mandatory = $true)][string]$TestOutput
)
$ErrorActionPreference = 'Stop'
$taskRepo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskTestRoot = [IO.Path]::GetFullPath($TestOutput).TrimEnd('\')
if (-not ($taskTestRoot.StartsWith((Join-Path $taskRepo '.private') + '\', [StringComparison]::OrdinalIgnoreCase) -or
          $taskTestRoot.StartsWith((Join-Path $taskRepo 'validation-results') + '\', [StringComparison]::OrdinalIgnoreCase))) {
    throw 'Tests must use a new directory under .private or validation-results.'
}
New-Item -ItemType Directory -Path $taskTestRoot -ErrorAction Stop | Out-Null
$taskTestMsysRoot = $Msys2Root
. (Join-Path $taskRepo 'build-install-windows.ps1')

$taskPath = Get-SetupPathValue 'C:\Windows;C:\Program Files\AdmixTools\bin\;D:\Tools;c:\program files\admixtools\bin' 'C:\Program Files\AdmixTools\bin'
if ($taskPath -ne 'C:\Program Files\AdmixTools\bin;C:\Windows;D:\Tools') { throw 'PATH duplicate/preservation check failed.' }
if ((Get-SetupPathValue '' 'C:\Example\bin') -ne 'C:\Example\bin') { throw 'Empty PATH check failed.' }
$taskMachinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
$taskUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$taskNativeFunction = (Get-Command Invoke-SetupCommand).ScriptBlock
$taskCalls = 0
$taskFailure = 'prepare'
function Invoke-SetupCommand {
    param([string]$Program, [string[]]$Arguments)
    $script:taskCalls++
    if ($Arguments -contains '-File') {
        $taskFileIndex = [Array]::IndexOf($Arguments, '-File') + 1
        $taskChild = $Arguments[$taskFileIndex]
        if ($taskChild.EndsWith('prepare-windows.ps1')) {
            if ($script:taskFailure -eq 'prepare') { throw 'Injected preparation failure' }
            return
        }
        if ($taskChild.EndsWith('build-windows.ps1')) {
            $taskSnapshot = Split-Path -Parent $taskChild
            Copy-Item -LiteralPath (Join-Path $BuiltInstallRoot 'bin') -Destination (Join-Path $taskSnapshot 'bin') -Recurse
            return
        }
        throw 'Unexpected child script in setup test'
    }
    if ($Program.EndsWith('python.exe')) {
        Copy-Item -LiteralPath (Join-Path $BuiltInstallRoot 'validation') -Destination $Arguments[-1] -Recurse
        return
    }
    if ($Program.EndsWith('qpAdm.exe')) {
        if ($script:taskFailure -eq 'success') { & $taskNativeFunction -Program $Program -Arguments $Arguments; return }
        throw 'Injected post-promotion smoke failure'
    }
    throw 'Unexpected child executable in setup test'
}

foreach ($taskMode in 'prepare', 'promote', 'success') {
    $taskFailure = $taskMode
    $taskTarget = Join-Path $taskTestRoot ($taskMode + ' existing install')
    New-Item -ItemType Directory -Path $taskTarget | Out-Null
    Copy-Item -LiteralPath (Join-Path $BuiltInstallRoot 'admixtools-install.json') -Destination $taskTarget
    [IO.File]::WriteAllText((Join-Path $taskTarget 'sentinel.txt'), 'Preserve previous installation.')
    $taskBefore = (Get-FileHash -LiteralPath (Join-Path $taskTarget 'admixtools-install.json')).Hash
    $taskCaught = $false
    try {
        Invoke-AdmixToolsSetup -SourceRoot $taskRepo -InstallRoot $taskTarget -Msys2Root $taskTestMsysRoot -PathScope None -NoInstallDependencies
    }
    catch {
        if ($_.Exception.Message -notmatch 'Injected.*failure') { throw }
        $taskCaught = $true
    }
    if ($taskMode -eq 'success') {
        if ($taskCaught) { throw 'Successful promotion unexpectedly failed.' }
        $taskUpdated = Get-Content -LiteralPath (Join-Path $taskTarget 'admixtools-install.json') -Raw | ConvertFrom-Json
        if ($taskUpdated.synthetic_cases -ne 35 -or $taskUpdated.synthetic_cases -is [array]) { throw 'Installation metadata has the wrong validation count.' }
        if (-not (Test-Path -LiteralPath (Join-Path $taskTarget 'bin\qpAdm.exe'))) { throw 'New installation is missing its payload.' }
        $taskRetained = @(Get-ChildItem -LiteralPath $taskTestRoot -Directory | Where-Object { $_.Name.StartsWith('success existing install.backup-') })
        if ($taskRetained.Count -ne 1 -or [IO.File]::ReadAllText((Join-Path $taskRetained[0].FullName 'sentinel.txt')) -ne 'Preserve previous installation.') {
            throw 'Successful upgrade did not retain its previous installation.'
        }
        continue
    }
    if (-not $taskCaught) { throw 'Injected setup failure was not propagated.' }
    if ([IO.File]::ReadAllText((Join-Path $taskTarget 'sentinel.txt')) -ne 'Preserve previous installation.' -or
        (Get-FileHash -LiteralPath (Join-Path $taskTarget 'admixtools-install.json')).Hash -ne $taskBefore) {
        throw "Previous installation was not preserved after $taskMode failure."
    }
}
Set-Item -Path function:Invoke-SetupCommand -Value $taskNativeFunction

$taskUnknown = Join-Path $taskTestRoot 'unrelated directory'
New-Item -ItemType Directory -Path $taskUnknown | Out-Null
[IO.File]::WriteAllText((Join-Path $taskUnknown 'keep.txt'), 'untouched')
$taskRefused = $false
try { Invoke-AdmixToolsSetup -SourceRoot $taskRepo -InstallRoot $taskUnknown -Msys2Root $taskTestMsysRoot -PathScope None -NoInstallDependencies }
catch { if ($_.Exception.Message -notmatch 'without an AdmixTools installation record') { throw }; $taskRefused = $true }
if (-not $taskRefused -or [IO.File]::ReadAllText((Join-Path $taskUnknown 'keep.txt')) -ne 'untouched') { throw 'Unrelated installation directory was not protected.' }

if ([Environment]::GetEnvironmentVariable('Path', 'Machine') -cne $taskMachinePath -or
    [Environment]::GetEnvironmentVariable('Path', 'User') -cne $taskUserPath) { throw 'Tests changed persistent PATH.' }
Write-Host 'PASS: PATH preservation, failure propagation, pre-build preservation, post-promotion rollback, successful upgrade/backup, and unrelated-folder refusal. No persistent PATH changes.'

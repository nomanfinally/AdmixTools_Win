[CmdletBinding()]
param(
    [string]$Msys2Root = 'C:\msys64',
    [string[]]$Tools = @(),
    [switch]$ListTools
)
$ErrorActionPreference = 'Stop'
$taskCompiler = Join-Path $Msys2Root 'ucrt64\bin\gcc.exe'
if (-not $ListTools -and -not (Test-Path -LiteralPath $taskCompiler)) {
    throw "UCRT64 GCC not found at $taskCompiler. See README.WINDOWS.md."
}
$taskOldPath = $env:PATH
try {
    $env:PATH = "$(Join-Path $Msys2Root 'ucrt64\bin');$env:PATH"
    $taskArgs = @((Join-Path $PSScriptRoot 'src\build_windows.py'))
    if ($ListTools) { $taskArgs += '--list' }
    else { $taskArgs += @('--toolchain', (Join-Path $Msys2Root 'ucrt64\bin')) }
    if ($Tools.Count) { $taskArgs += @('--tools') + $Tools }
    & python @taskArgs
    if ($LASTEXITCODE -ne 0) { throw "Windows build failed (exit $LASTEXITCODE)." }
}
finally { $env:PATH = $taskOldPath }

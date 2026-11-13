[CmdletBinding()]
param(
    [string]$Version = '8.1.0',
    [string]$BinaryDirectory = '',
    [string]$OutputDirectory = '',
    [string]$WixPath = '',
    [switch]$Rebuild,
    [string]$Msys2Root = 'C:\msys64'
)
$ErrorActionPreference = 'Stop'
if (-not $BinaryDirectory) { $BinaryDirectory = Join-Path $PSScriptRoot 'bin' }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $PSScriptRoot 'dist' }
if ($Rebuild) {
    & (Join-Path $PSScriptRoot 'build-windows.ps1') -Msys2Root $Msys2Root
    if ($LASTEXITCODE -ne 0) { throw 'Native build failed.' }
}
$taskArguments = @((Join-Path $PSScriptRoot 'packaging\windows\build_msi.py'),
    '--version', $Version, '--bin', $BinaryDirectory, '--output', $OutputDirectory,
    '--runtime-root', (Join-Path $Msys2Root 'ucrt64'))
if ($WixPath) { $taskArguments += @('--wix', $WixPath) }
& python @taskArguments
if ($LASTEXITCODE -ne 0) { throw 'MSI packaging failed. Read the diagnostics above.' }

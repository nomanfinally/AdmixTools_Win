[CmdletBinding()]
param(
    [string]$RepositoryRoot = '',
    [string]$Msys2Root = 'C:\msys64'
)
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) { $RepositoryRoot = $PSScriptRoot }
$taskRepository = (Resolve-Path -LiteralPath $RepositoryRoot -ErrorAction Stop).Path
$taskPublicGuide = Join-Path $taskRepository 'README.WINDOWS.md'
$taskPersonalGuide = Join-Path $taskRepository 'README.WINDOWS.personal.md'
if (-not (Test-Path -LiteralPath $taskPublicGuide -PathType Leaf)) {
    throw "Public guide not found: $taskPublicGuide"
}

# Fail closed if a checkout loses its privacy ignore rules.
& git -C $taskRepository check-ignore --quiet -- README.WINDOWS.personal.md
if ($LASTEXITCODE -ne 0) {
    throw 'The personal guide must be ignored by Git before it can be generated. Check .gitignore and ensure the file is not tracked.'
}

$taskMsysRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Msys2Root)
$taskLiteralRepo = "'" + $taskRepository.Replace("'", "''") + "'"
$taskLiteralBin = "'" + (Join-Path $taskRepository 'bin').Replace("'", "''") + "'"
$taskLiteralMsys = "'" + $taskMsysRoot.Replace("'", "''") + "'"
$taskText = [IO.File]::ReadAllText($taskPublicGuide)
$taskText = $taskText.Replace('# ADMIXTOOLS on Windows', '# ADMIXTOOLS on Windows - private local guide')
$taskText = $taskText.Replace('$Repo = Join-Path $env:USERPROFILE ''source\AdmixTools_Win''', ('$Repo = ' + $taskLiteralRepo))
$taskText = $taskText.Replace('$AdmixBin = Join-Path $env:USERPROFILE ''source\AdmixTools_Win\bin''', ('$AdmixBin = ' + $taskLiteralBin))
$taskText = $taskText.Replace('$Msys2Root = ''C:\msys64''', ('$Msys2Root = ' + $taskLiteralMsys))
$taskHeader = @"
<!-- PRIVATE: generated local instructions. Git ignores this file. Do not publish. -->

Generated from README.WINDOWS.md. Edit the public source for shared instructions,
then rerun New-PersonalWindowsGuide.ps1 with your local MSYS2 root.
This guide contains personal paths; do not attach it to a public issue or commit.

Local repository: $taskRepository
Local executable folder: $(Join-Path $taskRepository 'bin')
Local MSYS2 root: $taskMsysRoot

"@
[IO.File]::WriteAllText($taskPersonalGuide, ($taskHeader + "`r`n" + $taskText), (New-Object Text.UTF8Encoding $false))
Write-Host "Private guide written: $taskPersonalGuide"

[CmdletBinding()]
param([string]$Msys2Root = 'C:\msys64')
$ErrorActionPreference = 'Stop'
$taskCompiler = Join-Path $Msys2Root 'ucrt64\bin\gcc.exe'
if (-not (Test-Path -LiteralPath $taskCompiler)) {
    throw "Install MSYS2 UCRT64 GCC, GSL and OpenBLAS first. See README.WINDOWS.md."
}
$taskBuild = Join-Path $PSScriptRoot 'src\.windows'
$taskSource = Join-Path $taskBuild 'argp-source'
$taskVenv = Join-Path $taskBuild 'venv'
$taskPython = Join-Path $taskVenv 'Scripts\python.exe'
$taskOldPath = $env:PATH
$taskOldCC = $env:CC
function Invoke-BuildStep {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed (exit $LASTEXITCODE)." }
}
try {
    New-Item -ItemType Directory -Force -Path $taskBuild | Out-Null
    if (-not (Test-Path -LiteralPath $taskPython)) {
        Invoke-BuildStep python @('-m', 'venv', $taskVenv)
    }
    Invoke-BuildStep $taskPython @('-m', 'pip', 'install', 'meson==1.12.1', 'ninja==1.13.2')
    # Maintained GNU argp source, pinned independently of our upstream baseline.
    if (-not (Test-Path -LiteralPath $taskSource)) {
        Invoke-BuildStep git @('clone', 'https://github.com/argp-standalone/argp-standalone.git', $taskSource)
        Invoke-BuildStep git @('-C', $taskSource, 'checkout', '--detach', '8ded2bc942740b5d291e450af661c5090dc3ca38')
    }
    $taskRevision = & git -C $taskSource rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $taskRevision -ne '8ded2bc942740b5d291e450af661c5090dc3ca38') {
        throw 'Unexpected argp source revision. Use the pinned commit documented in this script.'
    }
    # The standalone parser retains glibc's older backtick quoting in this
    # diagnostic. Match the current Linux reference's straight single quotes.
    $taskParserFile = Join-Path $taskSource 'argp-parse.c'
    $taskParserText = [IO.File]::ReadAllText($taskParserFile)
    $taskOldDiagnostic = '%s: unrecognized option ' + [char]96 + "%s'\n"
    $taskParserText = $taskParserText.Replace($taskOldDiagnostic, "%s: unrecognized option '%s'\n")
    [IO.File]::WriteAllText($taskParserFile, $taskParserText, (New-Object Text.UTF8Encoding $false))
    $env:PATH = "$(Join-Path $taskVenv 'Scripts');$(Join-Path $Msys2Root 'ucrt64\bin');$taskOldPath"
    # Meson parses CC as a command, including the quotes for paths with spaces.
    $env:CC = '"' + $taskCompiler + '"'
    $taskArgpBuild = Join-Path $taskBuild 'argp-build'
    $taskArgpInstall = Join-Path $taskBuild 'argp'
    $taskMesonArgs = @('-m', 'mesonbuild.mesonmain', 'setup', $taskArgpBuild, $taskSource,
        '--prefix', $taskArgpInstall, '--libdir', 'lib', '--buildtype=release')
    if (Test-Path -LiteralPath (Join-Path $taskArgpBuild 'meson-private\coredata.dat')) {
        $taskMesonArgs += '--reconfigure'
    }
    Invoke-BuildStep $taskPython $taskMesonArgs
    Invoke-BuildStep $taskPython @('-m', 'mesonbuild.mesonmain', 'compile', '-C', $taskArgpBuild)
    Invoke-BuildStep $taskPython @('-m', 'mesonbuild.mesonmain', 'test', '-C', $taskArgpBuild, '--print-errorlogs')
    Invoke-BuildStep $taskPython @('-m', 'mesonbuild.mesonmain', 'install', '-C', $taskArgpBuild)
}
finally {
    $env:PATH = $taskOldPath
    $env:CC = $taskOldCC
}

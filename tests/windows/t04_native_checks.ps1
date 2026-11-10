[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Bin,
      [Parameter(Mandatory=$true)][string]$Fixtures,
      [Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = 'Stop'
$taskBin = (Resolve-Path -LiteralPath $Bin).Path
$taskFixtures = (Resolve-Path -LiteralPath $Fixtures).Path
$taskOutput = [IO.Path]::GetFullPath($Output)
if (Test-Path -LiteralPath $taskOutput) { throw 'Use a new evidence directory.' }
$null = New-Item -ItemType Directory -Path $taskOutput
$taskWork = Join-Path $taskOutput 'PowerShell space # native'
$null = New-Item -ItemType Directory -Path $taskWork
foreach ($taskName in @('input.geno','input.snp','input.ind','quads','input.geno.gz')) {
    Copy-Item -LiteralPath (Join-Path $taskFixtures $taskName) -Destination $taskWork
}
$taskUtf8 = New-Object Text.UTF8Encoding($false)
$taskParameters = "genotypename: input.geno`nsnpname: input.snp`nindivname: input.ind`npopfilename: quads`nblgsize: .005`n"
[IO.File]::WriteAllText((Join-Path $taskWork 'parameters with space.par'),$taskParameters,$taskUtf8)
$taskOldTemp = $env:STMP
$taskOldThreads = $env:OPENBLAS_NUM_THREADS
$taskOldOmp = $env:OMP_NUM_THREADS
$taskOldCore = $env:OPENBLAS_CORETYPE
$taskRecords = @{}
Push-Location -LiteralPath $taskWork
try {
    $env:OPENBLAS_NUM_THREADS = '1'
    $env:OMP_NUM_THREADS = '1'
    $env:OPENBLAS_CORETYPE = 'NEHALEM'
    $taskExe = Join-Path $taskBin 'qpDstat.exe'
    & $taskExe -p '.\parameters with space.par' > direct.stdout 2> direct.stderr
    $taskRecords['direct_exit'] = $LASTEXITCODE
    & $taskExe -p '.\parameters with space.par' 2> tee.stderr | Tee-Object -FilePath tee.stdout | Out-Null
    $taskRecords['tee_exit'] = $LASTEXITCODE
    $taskRecords['direct_results'] = @([IO.File]::ReadAllLines((Join-Path $taskWork 'direct.stdout')) | Where-Object { $_.StartsWith('result: ') })
    $taskRecords['tee_results'] = @([IO.File]::ReadAllLines((Join-Path $taskWork 'tee.stdout')) | Where-Object { $_.StartsWith('result: ') })
    $taskRecords['result_text_equal'] = (($taskRecords['direct_results'] -join "`n") -ceq ($taskRecords['tee_results'] -join "`n"))
    $taskTemp = Join-Path $taskWork 'temporary space'
    $null = New-Item -ItemType Directory -Path $taskTemp
    $env:STMP = $taskTemp.Replace('\','/')
    [IO.File]::WriteAllText((Join-Path $taskWork 'gzip.par'),$taskParameters.Replace('input.geno','input.geno.gz'),$taskUtf8)
    & $taskExe -p gzip.par > gzip.stdout 2> gzip.stderr
    $taskRecords['gzip_exit'] = $LASTEXITCODE
    $taskRecords['temporary_files'] = @(Get-ChildItem -LiteralPath $taskTemp | Select-Object -ExpandProperty Name)
    $taskRecords['gzip_results'] = @([IO.File]::ReadAllLines((Join-Path $taskWork 'gzip.stdout')) | Where-Object { $_.StartsWith('result: ') })
    $taskRecords['gzip_result_text_equal'] = (($taskRecords['direct_results'] -join "`n") -ceq ($taskRecords['gzip_results'] -join "`n"))
    $taskRecords['powershell_version'] = $PSVersionTable.PSVersion.ToString()
    $taskRecords['streams'] = @{}
    foreach ($taskFile in @('direct.stdout','direct.stderr','tee.stdout','tee.stderr','gzip.stdout','gzip.stderr')) {
        $taskRecords['streams'][$taskFile] = (Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash
    }
} finally {
    Pop-Location
    $env:STMP = $taskOldTemp
    $env:OPENBLAS_NUM_THREADS = $taskOldThreads
    $env:OMP_NUM_THREADS = $taskOldOmp
    $env:OPENBLAS_CORETYPE = $taskOldCore
}
$taskJson = ConvertTo-Json -InputObject $taskRecords -Depth 4
[IO.File]::WriteAllText((Join-Path $taskOutput 'powershell.json'),$taskJson,$taskUtf8)
if (-not $taskRecords.result_text_equal -or -not $taskRecords.gzip_result_text_equal -or
    $taskRecords.direct_exit -ne 0 -or $taskRecords.tee_exit -ne 0 -or $taskRecords.gzip_exit -ne 0 -or
    $taskRecords.temporary_files.Count -ne 0) { throw 'Native checks failed; inspect retained streams.' }

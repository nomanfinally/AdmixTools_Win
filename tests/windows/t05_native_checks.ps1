param([Parameter(Mandatory=$true)][string]$Binary,
      [Parameter(Mandatory=$true)][string]$Fixture,
      [Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = 'Stop'
$taskBinary = (Resolve-Path -LiteralPath $Binary).Path
$taskFixture = (Resolve-Path -LiteralPath $Fixture).Path
if (Test-Path -LiteralPath $Output) { throw 'Output must be new' }
$taskOutput = (New-Item -ItemType Directory -Path $Output).FullName
$taskWork = (New-Item -ItemType Directory -Path (Join-Path $taskOutput 'working directory with spaces')).FullName
foreach ($taskName in @('input.geno','input.snp','input.ind','triples','input.geno.gz')) {
    Copy-Item -LiteralPath (Join-Path $taskFixture $taskName) -Destination $taskWork
}
$taskOldPath=$env:PATH
$taskOldStmp=$env:STMP
$taskOldBlas=$env:OPENBLAS_NUM_THREADS
$taskOldOmp=$env:OMP_NUM_THREADS
$taskOldCore=$env:OPENBLAS_CORETYPE
try {
    $env:PATH="$(Split-Path -Parent $taskBinary);$env:PATH"
    $env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:OPENBLAS_CORETYPE='NEHALEM'
    Push-Location -LiteralPath $taskWork
    New-Item -ItemType Directory -Path tmp | Out-Null
    $env:STMP=(Join-Path $taskWork 'tmp').Replace('\','/')
    $taskPar="genotypename: input.geno`nsnpname: input.snp`nindivname: input.ind`npopfilename: triples`nseed: 77`nblgsize: .005`n"
    [IO.File]::WriteAllText((Join-Path $taskWork 'parameters with spaces'),$taskPar,(New-Object Text.UTF8Encoding($false)))
    & $taskBinary -p 'parameters with spaces' 1> direct.stdout 2> direct.stderr
    $taskDirectExit=$LASTEXITCODE
    & $taskBinary -p 'parameters with spaces' 2> tee.stderr | Tee-Object -FilePath tee.stdout | Out-Null
    $taskTeeExit=$LASTEXITCODE
    $taskGzip=$taskPar.Replace('input.geno','input.geno.gz')
    [IO.File]::WriteAllText((Join-Path $taskWork 'gzip.par'),$taskGzip,(New-Object Text.UTF8Encoding($false)))
    & $taskBinary -p gzip.par 1> gzip.stdout 2> gzip.stderr
    $taskGzipExit=$LASTEXITCODE
    $taskDirect=@(Get-Content direct.stdout | Where-Object { $_ -match '^ result:' })
    $taskTee=@(Get-Content tee.stdout | Where-Object { $_ -match '^ result:' })
    $taskGzipRows=@(Get-Content gzip.stdout | Where-Object { $_ -match '^ result:' })
    $taskResult=[ordered]@{
        powershell=$PSVersionTable.PSVersion.ToString(); architecture=$env:PROCESSOR_ARCHITECTURE
        direct_exit=$taskDirectExit; tee_exit=$taskTeeExit; gzip_exit=$taskGzipExit
        result_rows=@($taskDirect | ForEach-Object { "$_" }); tee_equal=(@(Compare-Object $taskDirect $taskTee).Count -eq 0)
        gzip_equal=(@(Compare-Object $taskDirect $taskGzipRows).Count -eq 0)
        stderr_empty=((Get-Item direct.stderr).Length -eq 0 -and (Get-Item tee.stderr).Length -eq 0 -and (Get-Item gzip.stderr).Length -eq 0)
        temporary_count=@(Get-ChildItem -LiteralPath tmp).Count
    }
    $taskResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskOutput 'results.json') -Encoding UTF8
    if ($taskDirectExit -ne 0 -or $taskTeeExit -ne 0 -or $taskGzipExit -ne 0 -or
        -not $taskResult.tee_equal -or -not $taskResult.gzip_equal -or -not $taskResult.stderr_empty -or
        $taskResult.temporary_count -ne 0 -or $taskDirect.Count -ne 2) { throw 'Native checks failed; see results.json' }
}
finally {
    Pop-Location
    $env:PATH=$taskOldPath; $env:STMP=$taskOldStmp; $env:OPENBLAS_NUM_THREADS=$taskOldBlas
    $env:OMP_NUM_THREADS=$taskOldOmp; $env:OPENBLAS_CORETYPE=$taskOldCore
}

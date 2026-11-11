param([Parameter(Mandatory=$true)][string]$Binary,
      [Parameter(Mandatory=$true)][string]$Fixture,
      [Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = 'Stop'
$taskBinary = (Resolve-Path -LiteralPath $Binary).Path
$taskFixture = (Resolve-Path -LiteralPath $Fixture).Path
if (Test-Path -LiteralPath $Output) { throw 'Output must be new' }
$taskOutput = (New-Item -ItemType Directory -Path $Output).FullName
$taskWork = (New-Item -ItemType Directory -Path (Join-Path $taskOutput 'working directory with spaces')).FullName
foreach ($taskName in @('input.geno','input.snp','input.ind','ratios','input.geno.gz')) {
    Copy-Item -LiteralPath (Join-Path $taskFixture $taskName) -Destination $taskWork
}
$taskSaved=@{}
foreach ($taskKey in @('PATH','STMP','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_CORETYPE')) {
    $taskSaved[$taskKey]=[Environment]::GetEnvironmentVariable($taskKey,'Process')
}
try {
    $env:PATH="$(Split-Path -Parent $taskBinary);$env:PATH"
    $env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:OPENBLAS_CORETYPE='NEHALEM'
    Push-Location -LiteralPath $taskWork
    New-Item -ItemType Directory -Path tmp | Out-Null
    $env:STMP=(Join-Path $taskWork 'tmp').Replace('\','/')
    $taskPar="genotypename: input.geno`nsnpname: input.snp`nindivname: input.ind`npopfilename: ratios`nblgsize: .005`n"
    [IO.File]::WriteAllText((Join-Path $taskWork 'parameters with spaces'),$taskPar,(New-Object Text.UTF8Encoding($false)))
    & $taskBinary -p 'parameters with spaces' 1> direct.stdout 2> direct.stderr
    $taskDirectExit=$LASTEXITCODE
    & $taskBinary -p 'parameters with spaces' 2> tee.stderr | Tee-Object -FilePath tee.stdout | Out-Null
    $taskTeeExit=$LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $taskWork 'gzip.par'),$taskPar.Replace('input.geno','input.geno.gz'),(New-Object Text.UTF8Encoding($false)))
    & $taskBinary -p gzip.par 1> gzip.stdout 2> gzip.stderr
    $taskGzipExit=$LASTEXITCODE
    $taskDirect=@(Get-Content direct.stdout | Where-Object { $_ -match '^ result:' })
    $taskTee=@(Get-Content tee.stdout | Where-Object { $_ -match '^ result:' })
    $taskGzipRows=@(Get-Content gzip.stdout | Where-Object { $_ -match '^ result:' })
    $taskTempLine=@(Get-Content gzip.stdout | Where-Object { $_ -match '^unzip cmd:' })
    $taskResult=[ordered]@{
        powershell=$PSVersionTable.PSVersion.ToString(); architecture=$env:PROCESSOR_ARCHITECTURE
        direct_exit=$taskDirectExit; tee_exit=$taskTeeExit; gzip_exit=$taskGzipExit
        result_rows=@($taskDirect | ForEach-Object { "$_" }); tee_equal=(@(Compare-Object $taskDirect $taskTee).Count -eq 0)
        gzip_equal=(@(Compare-Object $taskDirect $taskGzipRows).Count -eq 0)
        stderr_empty=((Get-Item direct.stderr).Length -eq 0 -and (Get-Item tee.stderr).Length -eq 0 -and (Get-Item gzip.stderr).Length -eq 0)
        temporary_count=@(Get-ChildItem -LiteralPath tmp).Count
        temp_command=@($taskTempLine | ForEach-Object { "$_" }); native_temp_path=($taskTempLine.Count -eq 1 -and $taskTempLine[0].Contains('\tmp\genotmp.'))
    }
    $taskResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskOutput 'results.json') -Encoding UTF8
    if ($taskDirectExit -ne 0 -or $taskTeeExit -ne 0 -or $taskGzipExit -ne 0 -or
        -not $taskResult.tee_equal -or -not $taskResult.gzip_equal -or -not $taskResult.stderr_empty -or
        -not $taskResult.native_temp_path -or $taskResult.temporary_count -ne 0 -or $taskDirect.Count -ne 1) {
        throw 'Native checks failed; see results.json'
    }
}
finally {
    Pop-Location
    foreach ($taskKey in $taskSaved.Keys) { [Environment]::SetEnvironmentVariable($taskKey,$taskSaved[$taskKey],'Process') }
}

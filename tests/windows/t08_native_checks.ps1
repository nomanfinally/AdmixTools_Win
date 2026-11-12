[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Bin,
      [Parameter(Mandatory=$true)][string]$Fixtures,
      [Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = 'Stop'
$taskBin = (Resolve-Path -LiteralPath $Bin).Path
$taskFixtures = (Resolve-Path -LiteralPath $Fixtures).Path
if (Test-Path -LiteralPath $Output) { throw 'Output must be new' }
$taskRoot = (New-Item -ItemType Directory -Path $Output).FullName
$taskWork = (New-Item -ItemType Directory -Path (Join-Path $taskRoot 'working directory Å with spaces')).FullName
Get-ChildItem -LiteralPath $taskFixtures -File | Where-Object { $_.Name -notlike 'graphtt*' } | Copy-Item -Destination $taskWork
$taskTemp = (New-Item -ItemType Directory -Path (Join-Path $taskWork 'native temp with spaces')).FullName
$taskOldPath = $env:PATH
$taskOldTemp = $env:STMP
$taskResult = @{ powershell=$PSVersionTable.PSVersion.ToString(); architecture=$env:PROCESSOR_ARCHITECTURE }
try {
    $env:PATH = "$taskBin;$env:PATH"
    $env:STMP = $taskTemp
    $env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:OPENBLAS_CORETYPE='NEHALEM'; $env:LC_ALL='C'
    Push-Location -LiteralPath $taskWork
    $taskParameters = "genotypename: input.geno`nsnpname: input.snp`nindivname: input.ind`nseed: 77`nblgsize: .005`ninbreed: NO`nhires: YES`ndiag: .0001`ninitmix: 12`ngraphname: graph`nfstatsname: input.fstats`n"
    [IO.File]::WriteAllText((Join-Path $taskWork 'par'),$taskParameters,(New-Object Text.UTF8Encoding $false))
    & (Join-Path $taskBin 'qpGraph.exe') -p par > direct.stdout 2> direct.stderr
    $taskResult.direct_exit=$LASTEXITCODE
    $taskLines = & (Join-Path $taskBin 'qpGraph.exe') -p par 2> tee.stderr | Tee-Object -FilePath tee.stdout
    $taskResult.tee_exit=$LASTEXITCODE
    $taskResult.tee_equal=([string]::Join("`n",$taskLines) -eq [string]::Join("`n",(Get-Content -LiteralPath tee.stdout)))
    $taskAuto=$taskParameters.Replace("fstatsname: input.fstats`n",'')
    [IO.File]::WriteAllText((Join-Path $taskWork 'auto.par'),$taskAuto,(New-Object Text.UTF8Encoding $false))
    & (Join-Path $taskBin 'qpGraph.exe') -p auto.par > auto.stdout 2> auto.stderr
    $taskResult.auto_exit=$LASTEXITCODE
    $taskGzip=$taskAuto.Replace('genotypename: input.geno','genotypename: input.geno.gz')
    [IO.File]::WriteAllText((Join-Path $taskWork 'gzip.par'),$taskGzip,(New-Object Text.UTF8Encoding $false))
    & (Join-Path $taskBin 'qpGraph.exe') -p gzip.par > gzip.stdout 2> gzip.stderr
    $taskResult.gzip_exit=$LASTEXITCODE
    $taskResult.scores=@{}
    foreach ($taskName in @('direct','auto','gzip')) {
        $taskResult.scores[$taskName]=[string[]]@(Get-Content -LiteralPath ($taskName+'.stdout') | Where-Object { $_ -match 'final score:|worst f-stat:|gslans:|final vg:' } | ForEach-Object { $_.ToString() })
    }
    $taskResult.scores_equal=(([string]::Join("`n",$taskResult.scores.direct) -eq [string]::Join("`n",$taskResult.scores.auto)) -and
        ([string]::Join("`n",$taskResult.scores.auto) -eq [string]::Join("`n",$taskResult.scores.gzip)))
    $taskResult.temp_native=(@(Get-Content -LiteralPath auto.stdout | Where-Object { $_ -like 'tmp: *' -and $_.Contains('\') -and -not $_.Contains('/') }).Count -eq 1)
    $taskResult.temp_clean=(@(Get-ChildItem -LiteralPath $taskTemp -Force).Count -eq 0)
    $taskResult.stderr_empty=(@('direct','tee','auto','gzip') | Where-Object { (Get-Item -LiteralPath ($_+'.stderr')).Length -gt 0 }).Count -eq 0
    & (Join-Path $taskBin 'qpreroot.exe') -g graph -w -o simplified.out > simplify.stdout 2> simplify.stderr
    $taskResult.simplify_exit=$LASTEXITCODE
    $taskResult.simplify_no_base_file=(-not (Test-Path -LiteralPath graphtt))
    $taskResult.simplify_no_temp=(@(Get-ChildItem -Filter 'graphtt*').Count -eq 0)
}
finally {
    Pop-Location
    $env:PATH=$taskOldPath; $env:STMP=$taskOldTemp
}
$taskResult | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $taskRoot 'results.json') -Encoding UTF8
$taskResult | ConvertTo-Json -Depth 7

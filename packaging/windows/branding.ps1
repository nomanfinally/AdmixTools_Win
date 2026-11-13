param([Parameter(Mandatory = $true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$taskInk = [Drawing.ColorTranslator]::FromHtml('#102b46')
$taskBlue = [Drawing.ColorTranslator]::FromHtml('#146b88')
$taskWhite = [Drawing.Brushes]::White

function Draw-Helix {
    param($Graphics, [single]$X, [single]$Y, [single]$Scale)
    $taskPen1 = New-Object Drawing.Pen ([Drawing.Color]::FromArgb(220, 101, 216, 224)), ([single](2.2 * $Scale))
    $taskPen2 = New-Object Drawing.Pen ([Drawing.Color]::FromArgb(220, 255, 255, 255)), ([single](2.2 * $Scale))
    $taskRung = New-Object Drawing.Pen ([Drawing.Color]::FromArgb(100, 255, 255, 255)), ([single]$Scale)
    try {
        for ($taskStep = 0; $taskStep -lt 70; ++$taskStep) {
            $taskA = [math]::Sin($taskStep / 11.0) * 15 * $Scale
            $taskB = [math]::Sin(($taskStep + 1) / 11.0) * 15 * $Scale
            $taskY1 = $Y + $taskStep * $Scale
            $Graphics.DrawLine($taskPen1, [single]($X + $taskA), [single]$taskY1, [single]($X + $taskB), [single]($taskY1 + $Scale))
            $Graphics.DrawLine($taskPen2, [single]($X - $taskA), [single]$taskY1, [single]($X - $taskB), [single]($taskY1 + $Scale))
            if ($taskStep % 7 -eq 0) {
                $Graphics.DrawLine($taskRung, [single]($X - $taskA), [single]$taskY1, [single]($X + $taskA), [single]$taskY1)
            }
        }
    }
    finally { $taskPen1.Dispose(); $taskPen2.Dispose(); $taskRung.Dispose() }
}

$taskDialog = New-Object Drawing.Bitmap 493, 312
$taskGraphics = [Drawing.Graphics]::FromImage($taskDialog)
$taskGraphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
$taskGraphics.Clear([Drawing.Color]::White)
$taskGradient = New-Object Drawing.Drawing2D.LinearGradientBrush ([Drawing.Rectangle]::new(0, 0, 164, 312)), $taskInk, $taskBlue, 90
$taskFont = New-Object Drawing.Font 'Segoe UI', 17, ([Drawing.FontStyle]::Bold)
$taskSmall = New-Object Drawing.Font 'Segoe UI', 8
try {
    $taskGraphics.FillRectangle($taskGradient, 0, 0, 164, 312)
    Draw-Helix $taskGraphics 81 32 1.4
    $taskGraphics.DrawString("ADMIX`nTOOLS", $taskFont, $taskWhite, 19, 149)
    $taskGraphics.DrawString("WINDOWS  /  X64", $taskSmall, $taskWhite, 20, 278)
    $taskDialog.Save((Join-Path $OutputDirectory 'dialog.bmp'), [Drawing.Imaging.ImageFormat]::Bmp)
}
finally { $taskGraphics.Dispose(); $taskDialog.Dispose(); $taskGradient.Dispose(); $taskFont.Dispose(); $taskSmall.Dispose() }

$taskBanner = New-Object Drawing.Bitmap 493, 58
$taskGraphics = [Drawing.Graphics]::FromImage($taskBanner)
try {
    $taskGraphics.Clear([Drawing.Color]::White)
    $taskBrush = New-Object Drawing.SolidBrush $taskInk
    $taskGraphics.FillRectangle($taskBrush, 435, 0, 58, 58)
    $taskGraphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    Draw-Helix $taskGraphics 464 10 0.55
    $taskBanner.Save((Join-Path $OutputDirectory 'banner.bmp'), [Drawing.Imaging.ImageFormat]::Bmp)
    $taskBrush.Dispose()
}
finally { $taskGraphics.Dispose(); $taskBanner.Dispose() }

$taskIcon = New-Object Drawing.Bitmap 48, 48
$taskGraphics = [Drawing.Graphics]::FromImage($taskIcon)
$taskMemory = New-Object IO.MemoryStream
try {
    $taskGraphics.Clear($taskInk)
    $taskGraphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    Draw-Helix $taskGraphics 24 5 0.53
    $taskIcon.Save($taskMemory, [Drawing.Imaging.ImageFormat]::Png)
    $taskBytes = $taskMemory.ToArray()
    $taskStream = [IO.File]::Create((Join-Path $OutputDirectory 'product.ico'))
    $taskWriter = New-Object IO.BinaryWriter $taskStream
    try {
        $taskWriter.Write([uint16]0); $taskWriter.Write([uint16]1); $taskWriter.Write([uint16]1)
        $taskWriter.Write([byte]48); $taskWriter.Write([byte]48); $taskWriter.Write([byte]0); $taskWriter.Write([byte]0)
        $taskWriter.Write([uint16]1); $taskWriter.Write([uint16]32)
        $taskWriter.Write([uint32]$taskBytes.Length); $taskWriter.Write([uint32]22); $taskWriter.Write($taskBytes)
    }
    finally { $taskWriter.Dispose(); $taskStream.Dispose() }
}
finally { $taskMemory.Dispose(); $taskGraphics.Dispose(); $taskIcon.Dispose() }

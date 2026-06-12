$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$specPath = Join-Path $projectRoot "packaging\windows\NAS Backup.spec"
$installerScript = Join-Path $projectRoot "packaging\windows\installer.iss"
$portableDir = Join-Path $projectRoot "release\portable"
$installerDir = Join-Path $projectRoot "release\installer"
$buildDir = Join-Path $projectRoot "build\pyinstaller"

Push-Location $projectRoot
try {
    Get-ChildItem -LiteralPath "app\ui" -Filter "*_ui.py" -File -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }

    New-Item -ItemType Directory -Force -Path $portableDir, $installerDir | Out-Null

    Write-Host "Building portable application with PyInstaller..."
    pyinstaller $specPath `
        --clean `
        --noconfirm `
        --distpath $portableDir `
        --workpath $buildDir
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller fallo con el codigo de salida $LASTEXITCODE."
    }

    $isccCommand = Get-Command iscc -ErrorAction SilentlyContinue
    $isccPath = if ($isccCommand) { $isccCommand.Source } else { $null }
    if (-not $isccPath) {
        $knownPaths = @(
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
            "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            "C:\Program Files\Inno Setup 6\ISCC.exe"
        )
        foreach ($path in $knownPaths) {
            if (Test-Path -LiteralPath $path) {
                $isccPath = $path
                break
            }
        }
    }

    if (-not $isccPath) {
        Write-Warning "Inno Setup no esta instalado o no esta en PATH."
        Write-Host "Portable application: release\portable\NAS Backup\NAS Backup.exe"
        exit 0
    }

    Write-Host "Building Windows installer with Inno Setup..."
    & $isccPath "/DProjectRoot=$projectRoot" $installerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup fallo con el codigo de salida $LASTEXITCODE."
    }
    Write-Host "Portable application: release\portable\NAS Backup\NAS Backup.exe"
    Write-Host "Installer: release\installer\NAS_Backup_Setup.exe"
}
finally {
    Pop-Location
}

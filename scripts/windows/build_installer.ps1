# Build the Windows installer: PyInstaller app folder + Inno Setup setup.exe.
# Requirements: Python 3.11, pipenv, Inno Setup 6 (iscc.exe on PATH or in the default folder).
# Output: build\CalendarDesktopNotifications-<version>-setup.exe

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$AppName = "CalendarDesktopNotifications"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

$env:PIPENV_IGNORE_VIRTUALENVS = "1"

function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe failed with exit code $LASTEXITCODE" }
}

$Version = (& pipenv run python -c "from src._version import __version__; print(__version__)").Trim()
if ($LASTEXITCODE -ne 0) { throw "Cannot read the app version" }
Write-Host "Building $AppName $Version for Windows"

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force build | Out-Null

$Icon = Join-Path $Root "build\app.ico"
Invoke-Checked pipenv @("run", "python", "scripts/windows/make_icon.py", $Icon)

# Windows shows the FileDescription of the exe as the app name in notifications
# and in Task Manager. Without a version resource it shows the exe file name.
$VersionParts = @([regex]::Matches($Version, "\d+") | ForEach-Object { $_.Value }) + @("0", "0", "0", "0")
$VersionTuple = ($VersionParts | Select-Object -First 4) -join ", "
$VersionFile = Join-Path $Root "build\version_info.txt"
@"
VSVersionInfo(
  ffi=FixedFileInfo(filevers=($VersionTuple), prodvers=($VersionTuple)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Calendar Desktop Notifications Contributors'),
      StringStruct('FileDescription', 'Calendar Notifications'),
      StringStruct('FileVersion', '$Version'),
      StringStruct('InternalName', '$AppName'),
      StringStruct('OriginalFilename', '$AppName.exe'),
      StringStruct('ProductName', 'Calendar Desktop Notifications'),
      StringStruct('ProductVersion', '$Version')
    ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@ | Set-Content -Path $VersionFile -Encoding ascii

# plyer and pystray pick their platform backend at runtime, and the app loads
# winsound through importlib. PyInstaller cannot see these imports. Without
# them, notifications, the tray icon or the notification sounds fail.
Invoke-Checked pipenv @(
    "run", "pyinstaller",
    "--noconfirm", "--clean", "--windowed",
    "--name", $AppName,
    "--icon", $Icon,
    "--version-file", $VersionFile,
    "--add-data", "sounds;sounds",
    "--hidden-import", "winsound",
    "--hidden-import", "plyer.platforms.win.notification",
    "--hidden-import", "plyer.platforms.win.libs.balloontip",
    "--hidden-import", "pystray._win32",
    "src/main.py"
)

$AppDir = Join-Path $Root "dist\$AppName"
if (-not (Test-Path (Join-Path $AppDir "$AppName.exe"))) { throw "PyInstaller output not found in $AppDir" }
# Without winsound in the bundle the app plays no notification sound.
if (-not (Get-ChildItem -Path $AppDir -Recurse -Filter "winsound*.pyd")) { throw "winsound is not in the bundle: $AppDir" }
if (-not (Get-ChildItem -Path $AppDir -Recurse -Filter "notification_*.wav")) { throw "Sound files are not in the bundle: $AppDir" }

$Iscc = (Get-Command iscc.exe -ErrorAction SilentlyContinue).Source
if (-not $Iscc) {
    $Iscc = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $Iscc) { throw "Inno Setup 6 not found. Install it: winget install JRSoftware.InnoSetup" }

Invoke-Checked $Iscc @(
    "/DAppVersion=$Version",
    "/DSourceDir=$AppDir",
    "/DIconFile=$Icon",
    "/DOutputDir=$(Join-Path $Root 'build')",
    "scripts\windows\installer.iss"
)

$Setup = Join-Path $Root "build\$AppName-$Version-setup.exe"
if (-not (Test-Path $Setup)) { throw "Installer not found: $Setup" }
Write-Host "Done: $Setup"

# Fetch Falcor into native/external (optional, large - do not vendor in git).
# Phase 0 helper for docs/plans/falcor-viewport-sam.md
param(
    [string]$Tag = "8.0",
    [string]$Dest = "",
    [switch]$Force,
    [switch]$FullHistory
)

$ErrorActionPreference = "Stop"

if (-not $Dest) {
    $Dest = Join-Path $PSScriptRoot "..\external\Falcor"
}
$Dest = [System.IO.Path]::GetFullPath($Dest)
$Parent = Split-Path $Dest -Parent

Write-Host "=== Slang_Falcon: fetch Falcor ==="
Write-Host "  tag/branch : $Tag"
Write-Host "  destination: $Dest"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git not found on PATH. Install Git for Windows, then re-run."
}

New-Item -ItemType Directory -Force -Path $Parent | Out-Null

if (Test-Path $Dest) {
    if (-not $Force) {
        Write-Host "Already exists: $Dest"
        Write-Host "Use -Force to remove and re-clone, or point CMake at this tree."
        if (Test-Path (Join-Path $Dest "CMakeLists.txt")) {
            Write-Host "Falcor CMakeLists.txt present - ready for Phase 0 CMake wiring."
        }
        exit 0
    }
    Write-Host "Removing existing tree (-Force)..."
    Remove-Item -Recurse -Force $Dest
}

$depthArgs = @()
if (-not $FullHistory) {
    $depthArgs = @("--depth", "1")
}

Write-Host "Cloning NVIDIAGameWorks/Falcor ($Tag) - this can take several minutes..."
git clone @depthArgs --branch $Tag `
    https://github.com/NVIDIAGameWorks/Falcor.git $Dest

if (-not (Test-Path (Join-Path $Dest "CMakeLists.txt"))) {
    Write-Error "Clone finished but CMakeLists.txt missing under $Dest - check tag $Tag."
}

Write-Host ""
Write-Host "Cloned Falcor -> $Dest"
Write-Host "Next:"
Write-Host "  1. Read native/README.md (Phase 0 build steps)"
Write-Host "  2. Standalone scaffold (no Falcor link yet):"
Write-Host '       cd native; cmake -B build -G "Visual Studio 17 2022" -A x64'
Write-Host "       cmake --build build --config Release"
Write-Host "  3. When ready to link Falcor (large): set SF_FALCOR_ROOT or -DSF_FETCH_FALCOR=ON"
Write-Host "       and follow Falcor packman/VS prerequisites from its README."

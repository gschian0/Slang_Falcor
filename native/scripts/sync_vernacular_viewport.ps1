# Sync VERNACULAR sample into Falcor tree and optionally configure/build.

param(
    [switch]$Configure,
    [switch]$Build,
    [string]$Config = "Release"
)

$ErrorActionPreference = "Stop"
$RepoNative = Split-Path $PSScriptRoot -Parent
$SampleSrc = Join-Path $RepoNative "samples\VernacularViewport"
$FalcorRoot = Join-Path $RepoNative "external\Falcor"
$SampleDst = Join-Path $FalcorRoot "Source\Samples\VernacularViewport"
$SamplesCmake = Join-Path $FalcorRoot "Source\Samples\CMakeLists.txt"

if (-not (Test-Path (Join-Path $FalcorRoot "CMakeLists.txt"))) {
    throw "Falcor not found at $FalcorRoot - run native\scripts\fetch_falcor.ps1 first."
}

Write-Host "Syncing VernacularViewport -> $SampleDst"
New-Item -ItemType Directory -Force -Path $SampleDst | Out-Null
Copy-Item -Force (Join-Path $SampleSrc "*") $SampleDst

$marker = "add_subdirectory(VernacularViewport)"
$cmakeText = Get-Content $SamplesCmake -Raw
if ($cmakeText -notmatch [regex]::Escape($marker)) {
    Add-Content -Path $SamplesCmake -Value "`n$marker`n"
    Write-Host "Patched Samples/CMakeLists.txt with $marker"
}
else {
    Write-Host "Samples/CMakeLists.txt already lists VernacularViewport"
}

# Also sync shaders into Source tree destination (already copied via Copy-Item * above,
# but ensure lessons/ lands even if Copy-Item was shallow in older runs).
$lessonsSrcSync = Join-Path $SampleSrc "lessons"
$lessonsDstSync = Join-Path $SampleDst "lessons"
if (Test-Path $lessonsSrcSync) {
    New-Item -ItemType Directory -Force -Path $lessonsDstSync | Out-Null
    Copy-Item -Force (Join-Path $lessonsSrcSync "*") $lessonsDstSync
}

if ($Configure) {
    Push-Location $FalcorRoot
    try {
        Write-Host "Running setup_vs2022.bat (submodules + packman + cmake)..."
        cmd /c "setup_vs2022.bat"
        if ($LASTEXITCODE -ne 0) {
            throw "setup_vs2022.bat failed ($LASTEXITCODE)"
        }
    }
    finally {
        Pop-Location
    }
}

if ($Build) {
    $buildDir = Join-Path $FalcorRoot "build\windows-vs2022"
    $cmake = Join-Path $FalcorRoot "tools\.packman\cmake\bin\cmake.exe"
    if (-not (Test-Path $cmake)) {
        throw "Packman cmake missing - run with -Configure first."
    }

    # SampleApp::run() always starts embedded Python and imports falcor.falcor_ext.
    Write-Host "Building FalcorPython (falcor_ext) + plugins ($Config)..."
    & $cmake --build $buildDir --config $Config --target FalcorPython
    if ($LASTEXITCODE -ne 0) {
        throw "FalcorPython build failed ($LASTEXITCODE)"
    }

    Write-Host "Building VernacularViewport ($Config)..."
    & $cmake --build $buildDir --config $Config --target VernacularViewport
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed ($LASTEXITCODE)"
    }
    $binRoot = Join-Path $buildDir "bin"
    $exe = Join-Path $binRoot "$Config\VernacularViewport.exe"
    if (-not (Test-Path $exe)) {
        $found = Get-ChildItem -Path $binRoot -Recurse -Filter VernacularViewport.exe -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $exe = $found.FullName }
    }

    $pluginsDir = Join-Path $binRoot "$Config\plugins"
    $assimp = Join-Path $pluginsDir "AssimpImporter.dll"
    if (-not (Test-Path $assimp)) {
        # Fallback if plugin targets were skipped somehow.
        New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null
        $vernacularPlugins = Join-Path $SampleSrc "plugins.json"
        if (Test-Path $vernacularPlugins) {
            Copy-Item -Force $vernacularPlugins (Join-Path $pluginsDir "plugins.json")
            Write-Host "Installed empty plugins.json (AssimpImporter.dll still missing)"
        }
    }
    else {
        Write-Host "Plugins present (AssimpImporter.dll OK) - leaving plugins.json alone"
    }

    # Falcor loads shaders from bin/<Config>/shaders/ — keep in sync with repo sources.
    $shaderDst = Join-Path $binRoot "$Config\shaders\Samples\VernacularViewport"
    New-Item -ItemType Directory -Force -Path $shaderDst | Out-Null
    Copy-Item -Force (Join-Path $SampleSrc "VernacularViewport.3d.slang") $shaderDst
    $lessonsSrc = Join-Path $SampleSrc "lessons"
    $lessonsDst = Join-Path $shaderDst "lessons"
    if (Test-Path $lessonsSrc) {
        New-Item -ItemType Directory -Force -Path $lessonsDst | Out-Null
        Copy-Item -Force (Join-Path $lessonsSrc "*") $lessonsDst
        Write-Host "Synced lesson kernels -> $lessonsDst"
    }
    Write-Host "Synced runtime shader -> $shaderDst"

    $ext = Join-Path $binRoot "$Config\python\falcor\falcor_ext.cp310-win_amd64.pyd"
    if (-not (Test-Path $ext)) {
        $ext = Join-Path $binRoot "$Config\python\falcor\falcor_ext.pyd"
    }
    Write-Host "falcor_ext: $(Test-Path $ext)  path=$ext"
    Write-Host "Built: $exe"
}

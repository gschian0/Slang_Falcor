# VERNACULAR native / Falcor host (Phase 2)

Load Phase 1 `SFMLP001` weights and run neural BRDF inference in a Falcor render
pass. Prefer **Vulkan Cooperative Vectors** (`VK_NV_cooperative_vector`) when
present; fall back to a scalar Slang MLP for debug.

**Product face:** VERNACULAR · **Package / C++ namespace:** `slang_falcon`  
**Related plan:** [docs/plans/falcor-viewport-sam.md](../docs/plans/falcor-viewport-sam.md) (Phase 0 = wire 3D host).  
**Round 1:** [docs/ROUND1.md](../docs/ROUND1.md) — Falcor mesh viewport is next round.
## Status

| Piece | State |
|-------|--------|
| Weight load / NeuralBrdfPass / HotReload | Scaffold in-tree (standalone exe) |
| Falcor fetch | `scripts/fetch_falcor.ps1` → `native/external/Falcor` (gitignored) |
| Falcor link / mesh viewport | Phase 0 — CMake hooks ready; full sample build is heavy (see below) |
| SAM / viewport AI | Not started (plan Phases 1–2) |

Falcor itself is **not** vendored (too large).

## Requirements

- Windows 10/11 + Visual Studio 2022 (MSVC)
- [Vulkan SDK](https://vulkan.lunarg.com/) (Falcor path)
- NVIDIA driver with CoopVec (RTX 20xx+ recommended for neural path)
- CMake ≥ 3.24
- Git (for fetch script)
- Python Phase 1 weights: `assets/weights/brdf_mlp.bin` (optional for scaffold smoke)

## Phase 0 — exact commands (practical path)

### A. Smoke the standalone scaffold (no Falcor download)

Validates weight load + pass stubs without cloning Falcor:

```powershell
cd d:\WindowsProgramming\Slang_Falcon\native
cmake -B build -G "Visual Studio 17 2022" -A x64 -DSF_BUILD_STANDALONE=ON
cmake --build build --config Release
.\build\Release\SlangFalconNative.exe --weights ..\assets\weights\brdf_mlp.bin
```

Expect: `Scaffold OK. Wire Falcor viewport next…`

### B. Fetch Falcor (large; several GB once packman runs)

```powershell
cd d:\WindowsProgramming\Slang_Falcon\native
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_falcor.ps1
# Optional: -Tag "8.0" (default)  |  -Force  |  -FullHistory
```

Tree lands at `native/external/Falcor`. Then follow **Falcor’s own README** for packman / dependencies (first Falcor configure is the long step).

### C. Configure this repo against a local Falcor tree

```powershell
cd d:\WindowsProgramming\Slang_Falcon\native
cmake -B build-falcor -G "Visual Studio 17 2022" -A x64 `
  -DSF_BUILD_STANDALONE=ON `
  -DSF_FETCH_FALCOR=OFF `
  -DSF_FALCOR_ROOT="$PWD\external\Falcor"
```

`SF_FALCOR_ROOT` must point at a Falcor checkout that already builds on your machine.
Until `SlangFalconFalcor` is fully wired to Falcor’s CMake targets, configure prints the Phase 0 checklist and still builds the standalone exe.

### D. VERNACULAR viewport + codebook (Phase 0 app)

Sample sources live in-repo (not only inside the Falcor clone):

- `native/samples/VernacularViewport/` — navigable SampleApp, sphere/cube/floor, Slang chapters
- Codebook: [`docs/codebook/never_ending_slang.md`](../docs/codebook/never_ending_slang.md)

```powershell
cd d:\WindowsProgramming\Slang_Falcor\native
# First time: sync sample into Falcor tree + packman/cmake (multi-GB, long)
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Configure -Build
# Later rebuilds (after editing sample sources):
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build
```

Run (typical output path after VS2022 preset):

```powershell
.\external\Falcor\build\windows-vs2022\bin\Release\VernacularViewport.exe
```

Controls: **WASD + mouse** navigate · **`[` `]`** codebook chapters · **F5** hot-reload · see HUD.

**Plugins / Python:** SampleApp always starts embedded Python (`falcor.falcor_ext`) and loads `plugins/plugins.json`. The sync script builds **`FalcorPython`** (and its plugin deps) before `VernacularViewport`. If you only built the sample earlier, re-run `-Build`.

Do **not** block on SAM — that is Phase 2 of the viewport plan.

## Features (scaffold)

| Feature | Module |
|---------|--------|
| Weight load (`SFMLP001`) | `src/WeightLoader.cpp` |
| Inference pass (CoopVec + scalar) | `src/NeuralBrdfPass.cpp`, `shaders/NeuralBrdf.slang` |
| Hot-reload `.slang` | `src/HotReload.cpp` (F5 / file watch) |
| Teacher ↔ neural toggle | `T` key — see Phase 2 train notes |
| Optional in-process training | `src/NeuralTrainPass.cpp` |
| Phase 0 Falcor viewport | `samples/VernacularViewport/` → synced into Falcor Samples |

## Layout

```
native/
  CMakeLists.txt
  README.md
  include/slang_falcon_native/
  src/
  shaders/
  scripts/fetch_falcor.ps1
  external/Falcor/          # gitignored; from fetch script
```

## Parity with Phase 1

Same feature packing and layer sizes as `docs/weight_format.md`.  
Exit criteria (Phase 0): BRDF MLP / lit Slang looks correct on a **3D mesh** in the Falcor viewport; toggle teacher vs neural with one key; hot-reload still works.

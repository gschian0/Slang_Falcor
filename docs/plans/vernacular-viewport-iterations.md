# VernacularViewport — iteration log

Track intentional scene / UX changes to the Falcor `VernacularViewport` sample.
Sample of record: `native/samples/VernacularViewport/`  
Rebuild: `native/scripts/sync_vernacular_viewport.ps1 -Build`

---

## Iteration 1 — 2026-08-04

### Intent / what user asked

Scene arrangement was “pretty good.” Do **not** overhaul the world. Only:

1. Centered **plane/quad** as the hero lesson surface  
2. **Double-sided** (visible from both faces)  
3. Clean **orbit** (RMB + wheel) around that plane  
4. Keep current water / looks fidelity  

### What changed

| File | Behavior |
|------|----------|
| `native/samples/VernacularViewport/VernacularViewport.cpp` | Hero mesh: `TriangleMesh::createCube` → `createQuad`. Node named `LessonPlane`, centered at `(0, 1.6, 0)`, rotation `(-90, 0, 0)` so the XZ unit quad stands vertical, uniform scale `3.2`. Orbit target = plane center (no Y offset). Pitch clamp widened (`-1.2` … `1.35`); zoom `2.5` … `28`. Hierarchy/Inspector label “Lesson Plane”. |
| `native/samples/VernacularViewport/VernacularViewport.h` | Defaults match centered vertical plane + orbit distance `8.5`. |
| *(unchanged)* `VernacularViewport.3d.slang` | Ocean / SurfaceKind / looks untouched. Cube path already flips `N` when `dot(N,V) < 0` so backface shading works with cull-none. |

**Double-sided how:** `StandardMaterial::setDoubleSided(true)` on MorphCube material (pre-existing) + scene `rasterize(..., CullMode::None)` (pre-existing). No duplicated flipped geometry.

**Preserved:** Material name still `MorphCube` for SurfaceKind dispatch; ocean / island / land / sky / lesson bank / folds unchanged.

### Keep vs revert

| Keep | Revert if |
|------|-----------|
| Quad hero + cull-none + doubleSided | User wants the morph **cube** mesh back |
| Orbit focus on `mCubePos` | Need a separate pivot / eye-height offset again |
| Water / looks shaders as-is | Never regress ocean for arrangement |

### Rebuild / run

```powershell
cd D:\WindowsProgramming\Slang_Falcor\native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build

cd D:\WindowsProgramming\Slang_Falcor\native\external\Falcor\build\windows-vs2022\bin\Release
.\VernacularViewport.exe
```

Controls: **RMB** orbit · **wheel** zoom · `[` `]` lessons · **F1** Hierarchy/Inspector · **F2** Lesson panel · prefer **F11** over F10 fullscreen.

### Water vs arrangement

- **Water:** untouched (ocean grid + `shadeOcean` path).  
- **Arrangement:** cube → centered vertical double-sided plane; orbit pivots on that plane.

---

## Docs side-quest (not a viewport iteration)

2026-08-04 — companion allegory [`docs/companion/robot_pinocchio_goes_rogue.md`](../companion/robot_pinocchio_goes_rogue.md) (focus vs information overload). No VernacularViewport code changes.

---

## Iteration 2 — 2026-08-04

### Intent / what user asked

Refocus VernacularViewport on the lost **Never-ending Slang / Vibration Modes of Cube** show. Environment/ocean studio is paused/secondary. Restore chapter looks with an explicit classic→physical shading ladder (monkey→ape→space monkey). Bring back finer orbit. No ORCA / PathTracer / commit.

### What changed

| Area | Behavior |
|------|----------|
| Scene | Four **5×5** mode grids `(1,1)(2,1)(1,2)(2,2)` + title cubes `VIBRATION` / `MODES OF` / `CUBE`; simple dark ground; no LessonPlane / island hero |
| Vertex | `gVertexWaves` / `gVibeAmp` standing waves; **V** / **,** **.** |
| Chapters | UV → Normals → Lambert → Blinn → **Physical** → splatter/brush/potluck/neural/jack-in/lit mixes (13 looks) |
| Orbit | Yaw/pitch ~`0.004`; wheel ~`0.3`; camera framed on show center |
| Docs | Codebook + RUNBOOK + CONTINUE NEXT; lesson-world plan marked paused/secondary |

**Preserved:** Analytic raster only (no `alphaTest`). F5 hot-reload. Sparse F1/F2 panels.

### Rebuild / run

```powershell
cd D:\WindowsProgramming\Slang_Falcor\native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build

cd D:\WindowsProgramming\Slang_Falcor\native\external\Falcor\build\windows-vs2022\bin\Release
.\VernacularViewport.exe
```

Controls: **RMB** orbit · **wheel** zoom · `[` `]` chapters · **V** waves · **,** **.** amp · **F1** / **F2** panels · **F5** reload.

### Keep vs revert

| Keep | Revert if |
|------|-----------|
| Vibration Modes as primary show | User asks to resume ocean/island studio as hero |
| Physical chapter in ladder | Ladder feels crowded — fold Physical into Blinn tip only |
| Fine orbit gains | Artists want snappier navigation again |

### Pin / restore (for Iteration 3+)

**Pinned 2026-08-04 as Iteration 2 show.** Not deleted — runtime `ShowMode::VibrationModes` (`F3` or F1 dropdown). Sources: `buildVibrationScene` + `gShowMode == 1` path in `VernacularViewport.3d.slang` + glyph title + mode grids. If the flag is ever removed, restore from this section + git history around Iteration 2 (`VernacularViewport.cpp` / `.3d.slang` / `shading_ladder.slang`).

---

## Iteration 3 — 2026-08-04

### Intent / what user asked

Pivot VernacularViewport to a mystical **Temple of Secret Knowledge** environment school: ocean bottom, distant computer-FBM land, sky (clouds + sun), three hero canvases (double-sided plane + sphere left + cube right), look bank `[` `]`, movement / env / water menus, delta-wave audio on Ch0 UV. Pin Vibration Modes (keep behind flag). Answer Omniverse compose path honestly. No Kit plugin, no Emerald Square, no commit.

### Philosophy (compose with research surfaces)

VERNACULAR should **compose with** Omniverse / USD / RTX research stacks (shaders, papers, USD) rather than rewriting engines. See [`vernacular-omniverse-bridge.md`](vernacular-omniverse-bridge.md).

**Will this work in Omniverse today?** No — host is Falcor `SampleApp`, not Kit. Portable pieces (Slang looks, analytic ocean/sky/land, future `.usda` layout) can travel; `VernacularViewport.exe` does not run inside Omniverse.

### What changed

| Area | Behavior |
|------|----------|
| Default show | **Temple School** — ethereal ocean (sp03 / ShaderToy spirit), FBM distant land, procedural sky, haze |
| Hero canvases | Center **LessonPlane** (double-sided), **LessonSphere** left, **LessonCube** right — shared look |
| Bank | 16 chapters: shading ladder 0–12 + school ports Ch13 circle / Ch14 shaping / Ch15 patterns |
| Pin | `ShowMode::TempleSchool` \| `VibrationModes` — **F3** toggles; Vibration scene builders retained |
| Movement | Orbit RMB+wheel (default); Fly WASD/QE stub via F1 menu |
| Menus (F1) | Show mode, movement, env (sun/haze/sky), water (scale/chop/color/absorb), mute |
| Audio MVP | WASAPI two-sine ~2 Hz beat on **Ch0 UV** only; **M** mute; graphics never blocked |

### Files

| Path | Role |
|------|------|
| `native/samples/VernacularViewport/VernacularViewport.{h,cpp,3d.slang}` | Dual-mode sample |
| `lessons/temple_env.slang` | Ocean / sky / land |
| `lessons/shading_ladder.slang` | Chapters + school ports |
| `docs/plans/vernacular-omniverse-bridge.md` | Omniverse honesty note |

### Rebuild / run

```powershell
cd D:\WindowsProgramming\Slang_Falcor\native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build

cd D:\WindowsProgramming\Slang_Falcor\native\external\Falcor\build\windows-vs2022\bin\Release
.\VernacularViewport.exe
```

### Controls (Temple)

| Input | Action |
|-------|--------|
| **RMB** + **wheel** | Orbit / zoom (Orbit mode) |
| **WASD QE** | Fly stub (F1 → Movement: Fly) |
| **[ ]** | Bank looks |
| **1–9** / **0** / **-** / **=** | Jump chapters (**=** cycles 11–15) |
| **F1** | Menus (show / move / env / water / mute) |
| **F2** | Station tip |
| **F3** | Toggle Temple ↔ Vibration Modes |
| **M** | Mute delta-wave audio |
| **F5** | Hot-reload |

### Audio / stubs

| Done | Stub / later |
|------|----------------|
| WASAPI float mix, ~120+122 Hz → ~2 Hz beat on Ch0 | Non-float mix formats stay silent |
| Mute + fail-soft if COM/endpoint fails | Omniverse spatial audio; richer bowls |
| | Full Kit/USD bridge; MaterialX mapping |

### Keep vs revert

| Keep | Revert if |
|------|-----------|
| Temple as default | User wants Vibration Modes primary again → default `ShowMode` or `F3` |
| Vibration behind `F3` | Drop pin only if user says delete |
| Analytic ocean PS raymarch | Perf too heavy — lower grid / iterations |

---

## Iteration 4 — 2026-08-04

### Intent / what user asked

Orbit / wheel felt dead in Temple show after Iteration 3. Restore **familiar** movement modes (Orbit + Fly) that actually work — no exotic schemes. Document as Iteration 4.

### Root cause

Falcor `MouseEvent::pos` is **normalized `[0,1]`**. Iteration 2 set yaw/pitch gain to `~0.004` (pixel-scale “finer” orbit). Full-width RMB drag ≈ **0.004 rad (~0.23°)** — orbit appeared broken. Wheel still worked when ImGui was not capturing; drag did not. Fly WASD existed but felt stubby (no usable look gain, no mode handoff, no speed boost).

Not ImGui F1 eating events by default (menus off → no capture); not Temple-only skip of `updateCamera`.

### What changed

| Area | Behavior |
|------|----------|
| Orbit (default) | RMB drag orbit + wheel zoom; look gain `2.8` rad/full-width; wheel `0.9` |
| Fly | WASD + QE + RMB look; **Shift** 3.5× speed; F1 fly-speed slider |
| Switch | **Tab** cycles Orbit ↔ Fly; F1 **Movement** dropdown with clear labels |
| Handoff | Mode switch syncs eye / orbit target so camera does not snap oddly |
| HUD | Shows current mode + mode-specific hint line |
| Docs | RUNBOOK + codebook + this log |

**Preserved:** Temple scene, look bank, F3 Vibration pin, audio MVP. No third exotic mode (only Orbit + Fly existed).

### Rebuild / run

```powershell
cd D:\WindowsProgramming\Slang_Falcor\native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build

cd D:\WindowsProgramming\Slang_Falcor\native\external\Falcor\build\windows-vs2022\bin\Release
.\VernacularViewport.exe
```

### Controls (movement)

| Input | Action |
|-------|--------|
| **RMB drag** | Orbit (Orbit) / look (Fly) |
| **Wheel** | Zoom (Orbit) |
| **WASD QE** | Fly · **Shift** faster |
| **Tab** | Orbit ↔ Fly |
| **F1 → Movement** | Same modes via dropdown |

### Keep vs revert

| Keep | Revert if |
|------|-----------|
| Normalized look gain ~2.8 | Artists want snappier/slower — tweak `kLookGain` only |
| Tab + F1 Orbit/Fly | User asks for Falcor built-in Orbiter/FirstPerson instead |

---

## Iteration 5 — 2026-08-09

### Intent / what user asked

Real **spatial audio engine** on VernacularViewport: spherical (omni) emission, distance attenuation, Doppler from relative velocity. Camera = listener. Keep **M** mute. Fail-soft (never block graphics). No FMOD / Omniverse / GPU audio / shader rewrite / commit.

### What changed

| Area | Behavior |
|------|----------|
| Engine | `VernacularSoundscape` — host physics + WASAPI shared mix (float32 / pcm16) |
| Listener | Eye pos / forward / up + finite-diff velocity from Orbit/Fly |
| Bowl | 3 sines (~0.5–4 Hz beat) on lesson plane (Temple) or vibe center; louder when looking at / near |
| Atmosphere | Quiet filtered-noise bed (Temple, distant) |
| Chirps | Slots 2–4 reserved, silent |
| Distance | `gain = clamp(ref/max(d,min),0,1)` then fade to 0 by maxDist (`min=1.5` `ref=4` `max=36` m) |
| Pan | Equal-power from listener-space azimuth |
| Doppler | `f' = f*(c+vL)/(c+vS)`, `c=343`, clamp 0.88–1.15; sources static; listener motion counts |
| Chapters | Ch0 = classic ~120/122 Hz; others slight f0 shift (same source) |
| F1 | Mute + master gain + Doppler checkbox + debug line |
| Backend | Extended Iteration 3 WASAPI instead of vendoring miniaudio into Falcor `/WX` |

**Preserved:** Temple default, F3 Vibration pin, Orbit/Fly, **M** mute, analytic shaders untouched.

### Files

| Path | Role |
|------|------|
| `native/samples/VernacularViewport/VernacularSoundscape.{h,cpp}` | Engine |
| `native/samples/VernacularViewport/VernacularViewport.{h,cpp}` | Camera → listener / F1 / lifecycle |
| `native/samples/VernacularViewport/CMakeLists.txt` | New compile unit |
| `docs/plans/vernacular-viewport-spatial-audio.md` | Design note |

### Rebuild / run

```powershell
cd D:\WindowsProgramming\Slang_Falcor\native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build

cd D:\WindowsProgramming\Slang_Falcor\native\external\Falcor\build\windows-vs2022\bin\Release
.\VernacularViewport.exe
```

### Keep vs revert

| Keep | Revert if |
|------|-----------|
| Spatial bowl on all chapters (f0 shift) | User wants Ch0-only silence again |
| WASAPI backend | Swap to miniaudio once isolated from `/WX` |
| Doppler clamp 0.88–1.15 | Artists want wilder fly-by |

### Stubs / later

Bird chirps · HRTF · moving emitters · Kit/Omniverse audio · Slang PCM.

---

## Iteration 6 — 2026-08-09

### Intent / what user asked

1. **Plane must be square** — look/texture must not stretch.  
2. **UV mapping scales with size** — texel / look frequency stays consistent when the plane (or canvases) change size (world-scale UVs, not 0–1 stretched across a resized quad).  
3. **Looks can have lighting modes** — Unlit vs Lambert / Blinn / Physical on the same banked look, using the temple sun.  
4. **Shapes reflect on the water where they actually are** — plane, sphere, cube visible in the ocean shader; simple contact / wet read; env + canvases share sun / haze.

Keep F3 Vibration pin, Orbit/Fly, Iteration 5 spatial audio. No Omniverse / ORCA / PathTracer. No commit.

### Root cause (plane stretch)

Falcor `createQuad` is an **XZ** unit square. Scale was `(3.4, 3.4, 1)` then `-90°` X — mesh **Z** becomes height and stayed `1`, so the hero was a **3.4 × 1** rectangle. UV 0–1 then stretched the look.

### What changed

| Area | Behavior |
|------|----------|
| Plane | Uniform scale `3.4` → vertical **square** after `-90°` X |
| UV | `worldScaleUv` — triplanar world meters, `frac` so 1 look tile ≈ 1 m on plane / sphere / cube |
| Lighting | **L** or F1 **Lighting mode**: Unlit / Lambert / Blinn / Physical; ladder + mode use `getSunDirection()` (same as sky / ocean) |
| Ocean | Analytic hit vs vertical quad + sphere + OBB cube along the reflection ray; cheap chapter look + light mode; contact wet under each footprint |
| CB | `gLightMode`, canvas centers / sizes, cube rotation axes — must match `.3d.slang` |

**Preserved:** Temple default, F3 Vibration, Orbit/Fly, spatial bowl (**M** mute), analytic raster.

### Files

| Path | Role |
|------|------|
| `native/samples/VernacularViewport/VernacularViewport.{h,cpp}` | Uniform plane, LightMode, CB, F1 / **L** |
| `native/samples/VernacularViewport/VernacularViewport.3d.slang` | Shared sun + canvas UV / light wrap |
| `lessons/shading_ladder.slang` | Temple-sun Lambert/Blinn/Physical + `applyLightMode` / `worldScaleUv` |
| `lessons/temple_env.slang` | Shape reflections + wet contact |

### Rebuild / run

```powershell
cd D:\WindowsProgramming\Slang_Falcor\native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build

cd D:\WindowsProgramming\Slang_Falcor\native\external\Falcor\build\windows-vs2022\bin\Release
.\VernacularViewport.exe
```

Kill `VernacularViewport.exe` first if the linker reports a locked file.

### Controls (new)

| Input | Action |
|-------|--------|
| **L** | Cycle Unlit → Lambert → Blinn → Physical |
| **F1 → Lighting mode** | Same modes via dropdown |

Orbit out over the water: plane / sphere / cube should appear in reflections under their true placement; dark wet patches under footprints. `[` `]` Ch0 UV on the square plane should not look stretched; **L** Lambert should share sun direction with the sky disk.

### Keep vs revert

| Keep | Revert if |
|------|-----------|
| Uniform plane scale | User wants a wide banner canvas — then non-uniform scale + world UVs (UVs still won’t stretch) |
| World-scale `frac` UV | Lesson wants a single 0–1 look across the whole plane — drop `frac`, keep `uv * size` or mesh UV |
| Water analytic reflections | Perf too heavy — skip chapter look, use flat albedo tint only |

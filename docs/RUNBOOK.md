# VERNACULAR RUNBOOK — boss edition

You are not guessing. This is the operating sheet.

**Repo:** `D:\WindowsProgramming\Slang_Falcor`  
**3D show (primary):** Falcor `VernacularViewport` — **Temple of Secret Knowledge** (Iteration 3, UV/light/water **Iteration 6**, upscale/boids **Iteration 7**, in-app editor + flock UI **Iteration 8**)  
**Pinned show:** **Vibration Modes of Cube** (Iteration 2) — `F3`  
**Camera:** Orbit / Fly (Iteration 4) — `Tab` or F1 → Movement  
**Audio:** Spatial bowl + distance / Doppler (Iteration 5) — **M** mute · boid chirps when **B**  
**Lighting:** Unlit / Lambert / Blinn / Physical (**L** or F1) — same sun as sky / ocean  
**Upscale:** Off / Internal scale / TAA (**U** or F1) — DLSS greyed (NGX / Mogwai)  
**School editor:** **F8** — in-Falcor ImGui VS / PS / CS / Diff (not live.py)  
**Boids:** **B** — compute flock + settings panel  
**Codebook:** [`codebook/never_ending_slang.md`](codebook/never_ending_slang.md) · [`codebook/gpu_school_passes.md`](codebook/gpu_school_passes.md)  
**Iterations:** [`plans/vernacular-viewport-iterations.md`](plans/vernacular-viewport-iterations.md)  
**Omniverse:** [`plans/vernacular-omniverse-bridge.md`](plans/vernacular-omniverse-bridge.md) — not Kit today; compose via Slang/USD later

---

## Daily — Temple of Secret Knowledge

### Rebuild

```powershell
cd D:\WindowsProgramming\Slang_Falcor\native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build
```

### Run

```powershell
cd D:\WindowsProgramming\Slang_Falcor\native\external\Falcor\build\windows-vs2022\bin\Release
.\VernacularViewport.exe
```

### What you get

| Layer | What |
|-------|------|
| **Ocean** | ShaderToy-style raymarched water (sp03 spirit), ethereal retune |
| **Distant land** | Computer-FBM hills / cliffs |
| **Sky** | Procedural dome — clouds + sun + haze |
| **Canvases** | Center **square** plane (double-sided), sphere left, cube right — world-scale UVs |
| **Bank** | UV → … → Physical → paint → school ports (circle / shaping / patterns) |
| **Water** | Ocean reflects plane / sphere / cube where they sit + soft wet contact |
| **Audio** | Spatial singing-bowl (plane) + quiet atmosphere; distance + stereo pan + Doppler (**M** mute) |
| **Pin** | **F3** → Vibration Modes lattices (Iteration 2) |

No Shader Man · no ORCA / PathTracer as primary · no claim of Omniverse Kit hosting.

### Controls

| Input | Action |
|-------|--------|
| **RMB drag** | Orbit (default) / look (Fly) |
| **Wheel** | Zoom (Orbit mode) |
| **WASD QE** | Fly move · **Shift** faster |
| **Tab** | Cycle **Orbit** ↔ **Fly** |
| **[ ]** | Bank looks |
| **1–9** | Chapters 0–8 |
| **0** | Chapter 9 |
| **-** | Chapter 10 |
| **=** | Cycle chapters 11–15 |
| **L** | Cycle lighting (Unlit / Lambert / Blinn / Physical) |
| **U** | Cycle upscale (Off / Internal / TAA) — DLSS unavailable |
| **B** | Toggle compute boids (Temple) |
| **F1** | Menus (show / Movement / Lighting / **Upscale** / boids / editor / env / water / mute) |
| **F2** | Chapter / station tip + school pass walkthrough |
| **F3** | Temple ↔ Vibration Modes |
| **F8** | Toggle in-app Slang editor (VS / PS / CS / Diff) — **E** is Fly-up · **Ctrl+S** save+reload |
| **M** | Mute audio |
| **F5** | Hot-reload shaders (also copies repo `lessons/` → shader cache) |
| **V** / **,** **.** | Waves / amp — Vibration mode only |

**Movement modes** (Iteration 4): **Orbit** (default) · **Fly**. Switch with **Tab** or F1 → Movement.

### Chapters (`[` `]`)

| # | Title | Notes |
|---|-------|--------|
| 0 | Hello UV | monkey — singing-bowl / delta bed (spatial) |
| 1 | World normals | monkey |
| 2 | Lambert | classic diffuse |
| 3 | Blinn-Phong | classic specular |
| 4 | **Physical** | GGX analytic |
| 5–12 | Paint / neural / mixes | ladder |
| 13 | Circle (sp02) | playground |
| 14 | Shaping (BoS) | school |
| 15 | Patterns (BoS) | school |

Sources: `native/samples/VernacularViewport/` · `lessons/temple_vs.slang` · `lessons/temple_ps.slang` · `lessons/temple_diff.slang` · `lessons/temple_env.slang` · `lessons/shading_ladder.slang` · [`codebook/gpu_school_passes.md`](codebook/gpu_school_passes.md)

### School walkthrough (Iteration 7)

How research apps do this — not a checkbox:

1. **Vertex** (`temple_vs.slang`) — vibration + ocean deck placement.  
2. **Pixel** (`temple_ps.slang`) — looks + **L** lighting + env.  
3. **Compute** (**B** boids) — agents/fields on CS; impostors rasterized after.  
4. **Differential** (`temple_diff.slang` in F8 Diff tab) — `[Differentiable]` / labs DiffSlang; **not in the 3D PSO** this pass (`bwd_diff` stays in labs / 2D live).  
5. **Upscale** — render low, reconstruct high. Internal blit always; TAA from depth mvec; **DLSS is NGX** (`DLSSPass.dll` + `nvngx_dlss.dll` already in bin). Greyed here: SampleApp has no Mogwai `RenderData`. Use the research SDK — don't rewrite UNIX.

**F8** toggles an **in-Falcor ImGui editor** on the files the sample compiled (`bin/.../shaders/Samples/VernacularViewport/lessons/` + repo `native/samples/VernacularViewport/lessons/`). **Ctrl+S** / Save writes both then hot-reloads (same as **F5**). Does **not** launch `live.py`.

### Exit checks

| Check | Pass |
|-------|------|
| Ocean + land + sky read as one place | Orbit out; haze soft; sun matches canvas **L** light |
| Plane / sphere / cube | Square plane (no stretch); sphere+cube do not cover plane |
| `[` `]` Ch0 UV | Looks update on all three; UV tiles ~1 m (not stretched 0–1) |
| Water reflections | Shapes appear under their true XZ; wet patches under footprints |
| F1 env / water / lighting | Sun, haze, chop, **L** change the world together |
| F1 Upscale Internal 0.67 | Softer / cheaper; TAA steadies shimmer when orbiting |
| F8 | In-app editor (not pygame); Save+reload updates Temple |
| B | Flock + settings; size mix; soft chirps (M mutes) |
| F3 | Vibration Modes grids restore |
| M | Spatial bowl mutes; graphics keep running |

---

## Lessons (2D)

```powershell
cd D:\WindowsProgramming\Slang_Falcor
.\.venv\Scripts\Activate.ps1
python -m slang_falcon.live
```

Prefer **F11**; avoid **F10**.

---

## Breakage

| Symptom | Fix |
|---------|-----|
| `gPad` / No member / wrong look | Rebuild — C++ CB must match `.3d.slang` |
| Failed to link | Analytic path only (no `alphaTest`) |
| Include `temple_env.slang` / ladder missing | `-Build` syncs `lessons/` into shader cache |
| HUD dumps `!"#$%` | ASCII-only HUD (already sanitized) |
| Stale shaders | `-Build` + delete `bin/Release/.shadercache` |
| Exe locked | Kill `VernacularViewport.exe` then rebuild |
| No audio | WASAPI fail-soft — check F1 status / debug line; graphics OK |

*Pinned: Temple School primary · Vibration Modes on F3 · analytic raster · Omniverse compose later · no ORCA.*

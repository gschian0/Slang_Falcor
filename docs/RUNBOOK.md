# VERNACULAR RUNBOOK — boss edition

You are not guessing. This is the operating sheet.

**Repo:** `D:\WindowsProgramming\Slang_Falcor`  
**3D show (primary):** Falcor `VernacularViewport` — **Temple of Secret Knowledge** (Iteration 3)  
**Pinned show:** **Vibration Modes of Cube** (Iteration 2) — `F3`  
**Camera:** Orbit / Fly (Iteration 4) — `Tab` or F1 → Movement  
**Audio:** Spatial bowl + distance / Doppler (Iteration 5) — **M** mute  
**Codebook:** [`codebook/never_ending_slang.md`](codebook/never_ending_slang.md)  
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
| **Canvases** | Center plane (double-sided), sphere left, cube right — shared look bank |
| **Bank** | UV → … → Physical → paint → school ports (circle / shaping / patterns) |
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
| **F1** | Menus (show / **Movement** / env / water / mute / gain / Doppler) |
| **F2** | Chapter / station tip |
| **F3** | Temple ↔ Vibration Modes |
| **M** | Mute audio |
| **F5** | Hot-reload shaders |
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

Sources: `native/samples/VernacularViewport/` · `lessons/temple_env.slang` · `lessons/shading_ladder.slang`

### Exit checks

| Check | Pass |
|-------|------|
| Ocean + land + sky read as one place | Orbit out; haze soft |
| Plane / sphere / cube | Sphere+cube do not cover plane |
| `[` `]` Ch0 UV | Looks update on all three canvases |
| F1 env / water | Sun, haze, chop change the world |
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

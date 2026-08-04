# VERNACULAR RUNBOOK — boss edition

You are not guessing. This is the operating sheet.

**Repo:** `D:\WindowsProgramming\Slang_Falcor`  
**3D school:** Falcor `VernacularViewport` — abstract studio (lesson cube on island)  
**Plan:** [`plans/vernacular-3d-lesson-world.md`](plans/vernacular-3d-lesson-world.md)

---

## Daily — abstract studio

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
| **Morph cube** | Lesson canvas in front of you — UV / ocean / plasma / circle / **Gaussian network** |
| **Island** | Shader-shaded ground plane under the cube (Gaussian look also tints it) |
| **Distant land** | Horizon hills / shore silhouette |
| **Ocean / sky** | sp03 waves + clouds + atmosphere |
| **Folds** | J Julia · M Mandelbrot · 0 off |
| **Lesson panel** | Optional F2 — curriculum `.slang` text |
| **Hierarchy / Inspector** | Optional F1 — decluttered by default |

No Shader Man · no WASD walk · no beacon gameplay.

### Controls

| Input | Action |
|-------|--------|
| **RMB drag** | Orbit camera around the cube |
| **Wheel** | Zoom |
| **[ ]** or **← →** (panels closed) | Bank lesson looks on the cube |
| **J** / **M** / **0** | Julia fold / Mandelbrot burst / folds off |
| **P** | Light presets |
| **L** | Optional 2D live editor for active lesson |
| **F1** | Toggle Hierarchy + Inspector |
| **F2** | Toggle Lesson code panel |
| **1 / 2 / 3** | Transform tool (with F1 open): Move / Rotate / Scale |

### Lessons on the cube (`[` `]`)

| Look | Title | Notes |
|------|-------|-------|
| 0 | Hello UV | Analytic UV faces |
| 1 | Ocean world | Micro sp03 on cube |
| 2 | Shaping / plasma | Plasma energy |
| 3 | Circle / polar | Polar ring |
| 4 | **Gaussian network** | 3D sibling of `sp06_gsplat2d` |

**Gaussian network knobs** (F1 → select Morph Cube or Island, or F2 Lesson panel when look 4 is active):

| Param | Meaning |
|-------|---------|
| Blob count | 1–8 Gaussians in the mixture |
| Sigma | Base spread |
| Amplitude | Per-blob strength |
| Layer depth | Stack separation along face depth |
| Mix / gain | Network blend weight |
| Anim speed | Orbit / drift of centers |
| Spread XYZ | Anisotropic sigma scales |
| Color A / B / C | Palette cycling across blobs |

2D source of record: `labs/slang_playground/shaders/sp06_gsplat2d.slang` (also NG03 fit: `labs/neural_gfx_afternoon/shaders/ng03_gaussian_fit.slang`).

### Later (planned)

TTS speak blurbs → NPU/local LLM generate text → hot-reload edited slang into the cube pass → SAM — same plan doc.

---

## Lessons (2D)

```powershell
cd D:\WindowsProgramming\Slang_Falcor
.\.venv\Scripts\Activate.ps1
python -m slang_falcon.live
```

Prefer **F11**; avoid **F10**.

**Color panel:** when the entry declares color-like `float3`/`float4` params (`color`, `albedo`, `tint`, `color_a`/`color_b`, …), a strip under the lesson banner exposes swatches + HSV + RGB. Hover `float3` / the param name in the editor to focus that picker. Try `slang_playground/sp01_simple_color` or `bos/03_colors`. **Simple Image** (`sp16_simple_image`) samples `labs/slang_playground/assets/cowboy_hat.png`.

---

## Breakage

| Symptom | Fix |
|---------|-----|
| `gPad` / No member | Rebuild — C++ CB must match `.3d.slang` |
| Failed to link | Analytic path only (no `alphaTest`) |
| Stale shaders | `-Build` + delete `bin/Release/.shadercache` |

*Pinned: abstract studio · [ ] bank lessons · J/M folds · RMB orbit · Gaussian network look 4.*

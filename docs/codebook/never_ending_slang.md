# Never-ending Slang — VERNACULAR codebook (Falcor 3D)

> Living story in Slang. **Default show:** Temple of Secret Knowledge (Iteration 3+6+7).  
> **Pinned:** Vibration Modes of Cube (Iteration 2) — toggle **F3**.  
> **How to run:** [`../RUNBOOK.md`](../RUNBOOK.md) · iterations [`../plans/vernacular-viewport-iterations.md`](../plans/vernacular-viewport-iterations.md)  
> **Pass school:** [`gpu_school_passes.md`](gpu_school_passes.md) — VS / PS / CS / autodiff / upscale walkthrough.

**Host:** `VernacularViewport`  
**Shader:** `native/samples/VernacularViewport/VernacularViewport.3d.slang`  
**Vertex / pixel school:** `lessons/temple_vs.slang` · `lessons/temple_ps.slang`  
**Autodiff (2D live):** `lessons/temple_diff.slang`  
**Env kernels:** `lessons/temple_env.slang`  
**Looks:** `lessons/shading_ladder.slang`  
**2D sister:** `python -m slang_falcon.lessons` · **F8** school window: `python -m slang_falcon.live --school-3d`

---

## Temple of Secret Knowledge (active)

- Ethereal ocean (raymarched, sp03 / ShaderToy spirit)  
- Distant computer-FBM land  
- Procedural sky (clouds + sun) + haze  
- Hero canvases: **square plane** (center, double-sided), **sphere** (left), **cube** (right) — shared chapter look, **world-scale UVs** (1 tile ≈ 1 m)  
- Lighting modes (**L** / F1): Unlit · Lambert · Blinn · Physical — same `getSunDirection()` as sky / ocean  
- Ocean reflects the three canvases at their true placement + contact wet — Iteration 6  
- Spatial singing-bowl on the lesson plane (distance + pan + Doppler; **M** mute) — Iteration 5  
- **Upscale** Off / Internal / TAA (**U**) — render low, reconstruct high; DLSS = NGX, greyed in SampleApp — Iteration 7  
- **F8** shader school window (VS / PS / Diff tabs) · **B** compute boids over ocean/sky — Iteration 7

## Vibration Modes of Cube (pinned)

- Four **5×5** mode grids `(1,1)(2,1)(1,2)(2,2)` + title cubes  
- Vertex standing waves (`V` · `,` `.`)  
- Restore: **F3** or F1 Show mode — code kept in `buildVibrationScene` / `gShowMode == 1`

## Shading ladder (monkey → ape → space monkey)

| Stage | Chapters | Message |
|-------|----------|---------|
| **Monkey** | UV, Normals | See the surface — coordinates and orientation |
| **Ape walking** | Lambert, Blinn-Phong | Classic shading *properties* |
| **Space monkey** | Physical | Full / Disney-ish analytic BRDF |
| **School ports** | Circle, Shaping, Patterns | Playground / BoS on the canvases |

## Chapters

| Key | Chapter | Look |
|-----|---------|------|
| 1 | Ch0 Hello UV | UV debug (+ spatial bowl) |
| 2 | Ch1 Normals | normal remap |
| 3 | Ch2 Lambert | diffuse clay |
| 4 | Ch3 Blinn | specular lobe |
| 5 | Ch4 Physical | GGX analytic |
| 6–0 / - / = | Ch5–15 | paint, neural, school ports |

Controls: `[` `]` · **L** lighting · **U** upscale · **B** boids · **Tab** Orbit/Fly · **F3** show · **F8** editor · RMB orbit · **F1** menus · **F5** reload — full table in RUNBOOK. Walk the passes in [`gpu_school_passes.md`](gpu_school_passes.md).

---

*Extend by adding a chapter helper + bumping `kChapterCount` + RUNBOOK row.*

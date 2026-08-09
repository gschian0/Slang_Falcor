# Never-ending Slang — VERNACULAR codebook (Falcor 3D)

> Living story in Slang. **Default show:** Temple of Secret Knowledge (Iteration 3).  
> **Pinned:** Vibration Modes of Cube (Iteration 2) — toggle **F3**.  
> **How to run:** [`../RUNBOOK.md`](../RUNBOOK.md) · iterations [`../plans/vernacular-viewport-iterations.md`](../plans/vernacular-viewport-iterations.md)

**Host:** `VernacularViewport`  
**Shader:** `native/samples/VernacularViewport/VernacularViewport.3d.slang`  
**Env kernels:** `lessons/temple_env.slang`  
**Looks:** `lessons/shading_ladder.slang`  
**2D sister:** `python -m slang_falcon.lessons`

---

## Temple of Secret Knowledge (active)

- Ethereal ocean (raymarched, sp03 / ShaderToy spirit)  
- Distant computer-FBM land  
- Procedural sky (clouds + sun) + haze  
- Hero canvases: **plane** (center, double-sided), **sphere** (left), **cube** (right) — shared chapter look  
- Spatial singing-bowl on the lesson plane (distance + pan + Doppler; **M** mute) — Iteration 5

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

Controls: `[` `]` · **Tab** Orbit/Fly · **F3** show · RMB orbit · **F1** menus · **F5** reload — full table in RUNBOOK.

---

*Extend by adding a chapter helper + bumping `kChapterCount` + RUNBOOK row.*

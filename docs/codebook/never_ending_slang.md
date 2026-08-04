# Never-ending Slang — VERNACULAR codebook (Falcor 3D)

> Living story in Slang on the **Vibration Modes of Cube** show.  
> **How to run (boss sheet):** [`../RUNBOOK.md`](../RUNBOOK.md)

**Host:** `VernacularViewport`  
**Shader:** `native/samples/VernacularViewport/VernacularViewport.3d.slang`  
**2D sister:** `python -m slang_falcon.lessons`

---

## Scene

- Four **5×5 cube rectangles** — standing-wave modes `(1,1) (2,1) (1,2) (2,2)` left→right  
- Title **written with cubes:** `VIBRATION` / `MODES OF` / `CUBE`  
- **Vertex shader** modulates positions with wave functions (`gVertexWaves`, `gVibeAmp`)

## Chapters

| Key | Chapter | Look |
|-----|---------|------|
| 1 | Ch0 Hello UV | UV debug |
| 2 | Ch1 Normals | normal remap |
| 3 | Ch2 Lambert | clay |
| 4 | Ch3 Blinn | highlight |
| 5 | Ch4 Splatter paint | Gaussian blobs |
| 6 | Ch5 Soft brush | paint trail |
| 7 | Ch6 Potluck | hash palette |
| 8 | Ch7 Neural | tiny 3→8→3 net |
| 9 | Ch8 Jack-in-box vibe | sharp envelope + mode viz |
| 0 | Ch9 Splatter lit | lit splatter |
| | Ch10 Neural lit | neural × Blinn |
| | Ch11 Potluck neon | mix |

Controls: `[` `]` · `V` waves · `,` `.` amplitude · **F5** reload — full table in RUNBOOK.

---

*Extend by adding a chapter helper + bumping `kChapterCount` + RUNBOOK row.*

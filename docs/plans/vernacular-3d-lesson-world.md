# Plan: VERNACULAR 3D environment shading school (Falcor)

**Status:** **Active as Temple of Secret Knowledge** (Iteration 3, 2026-08-04) — Falcor `VernacularViewport` default show. Vibration Modes of Cube pinned on `F3` (Iteration 2). Omniverse: compose later — [`vernacular-omniverse-bridge.md`](vernacular-omniverse-bridge.md).  
**Product (this plan):** Falcor as **environment shading school** — sky / ocean / distant land / canvases as teaching surfaces.  
**2D live** (`slang_falcon.live`) stays the deep editor / curriculum bank.

Related: [falcor-viewport-sam.md](falcor-viewport-sam.md) · [llm-slang-torch-realtime.md](llm-slang-torch-realtime.md) · [manifesto.md](../manifesto.md) · [RUNBOOK.md](../RUNBOOK.md)

---

## Product lock

- **No** Shader Man / WASD walk / beacon scavenger hunt as the primary loop.
- Composition: **shader cube in front**, **island under**, **ocean framing**, **distant land**, **procedural sky** — orbit camera.
- Lessons: **left/right bank** (`[` `]`). `L` = optional 2D escape hatch.
- Julia / Mandelbrot folds + Gaussian network are first-class looks.
- Analytic-only raster path until proven (no `alphaTest` / material-eval link traps).

---

## Sequence

### Phase 0 — Docs truth *(this file + AGENTS / CONTINUE / RUNBOOK)*

Abstract studio is of record; walkable Phase A (Shader Man) is archived intent only.

### Phase 1 — Stable shading architecture

- Per-material `SurfaceKind` dispatch (not distance heuristics).
- Layered `shadeSky` / `shadeOcean` / `shadeIsland` / `shadeCube` / `shadeLand`.
- Documented `PerFrameCB` contract mirrored in C++.

### Phase 2 — Environment fidelity

- Coherent sky + ocean + island wet edge + distant land + cube canvas.
- Atmosphere desk on Environment object (F1).

### Phase 3 — Curriculum as real looks

- Data-driven lesson table aligned with `labs/curriculum.json` ids.
- Shared kernels under `native/samples/VernacularViewport/lessons/`.
- F2 shows active module source.

### Phase 4 — Hot-reload bridge

- Sync script copies lesson modules into Falcor shader tree.
- Hot-reload recreates raster pass; `L` still opens 2D live.

### Phase 5 — Sparse school UX

- Presentation mode: HUD bank strip; F1 Environment/Inspector; F2 code.
- Exit checks in RUNBOOK.

### Later (after the loop is fun)

| Track | Intent |
|-------|--------|
| **TTS / NPU text** | Speak blurbs; local LLM expands tips ([llm-slang-torch-realtime.md](llm-slang-torch-realtime.md)) |
| **SAM / viewport AI** | [falcor-viewport-sam.md](falcor-viewport-sam.md) |
| **Inline AI image models + filters** | Generate / transform textures in-viewport (cube or island canvas) without leaving Falcor |
| **Inline post-process shaders** | Bankable fullscreen / camera post chain (bloom, grade, feedback) as curriculum looks — Vsynth-adjacent |

### Falcor ecosystem leverage (optional later labs)

Do **not** block the analytic environment school on these. When ready, Mogwai + render graphs teach “real” production shading:

| Asset / feature | Why it matters for VERNACULAR | Notes |
|-----------------|-------------------------------|--------|
| [NVIDIA Emerald Square (ORCA)](https://developer.nvidia.com/orca/nvidia-emerald-square) | Dense city for path-trace / visibility / material literacy | ~10M tris; **CC BY-NC-SA 3.0** (non-commercial share-alike) |
| [SpeedTree ORCA pack](https://developer.nvidia.com/orca/speedtree) | Vegetation / alpha / wind-facing lessons next to our island | FBX; same **CC BY-NC-SA 3.0** |
| Falcor [Path Tracer](https://github.com/NVIDIAGameWorks/Falcor/blob/master/docs/usage/getting-started.md) + NRD / RTXDI | Unbiased GI, nested dielectrics, MIS — contrast with our analytic ocean/sky | Load via Mogwai scripts (`PathTracer.py` / `PathTracerNRD.py`) |
| [Render passes](https://raw.githubusercontent.com/NVIDIAGameWorks/Falcor/master/docs/usage/render-passes.md) | Compose school “looks” as graph nodes (post, accumulate, tone map) | Plugin `registerPlugin`; dictionary between passes |
| Scene formats (USD / Assimp FBX-GLTF / `.pyscene`) | Drop ORCA or Arcade into a lab without rewriting SampleApp | `.pyscene` can tweak materials / EnvMap / lights at load |

**Agency pin:** ORCA is research/teaching content under NC-SA — fine for school demos, not for shipping a closed commercial look that redistributes the meshes. Our analytic studio stays the default IP you own.

---

## Non-goals (now)

- Walkable RPG school
- 2D live chrome redesign
- Full path-traced Falcor materials as the lesson path

---

## Exit checks

| Phase | Done when |
|-------|-----------|
| 1 | Inspector moves cube/island/land; shading identity stays correct |
| 2 | Orbit-out reads as one place (sky/water/island/cube/horizon) |
| 3 | `[` `]` names real curriculum ids; F2 shows module source |
| 4 | Edit active lesson `.slang`, cube updates after hot-reload |
| 5 | HUD bank strip + F1/F2 roles match RUNBOOK |

*Pinned: environment school first → hot-reload → voice/NPU → SAM → AI image + post.*

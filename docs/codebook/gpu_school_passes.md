# GPU school passes — how VERNACULAR walks the ladder

Temple is not a checkbox farm. Open the files, change them, F5. This is how research apps actually ship VS / PS / CS / autodiff / upscale.

**Host:** `VernacularViewport.exe` · **2D sister:** `python -m slang_falcon.live` · **Run:** [`../RUNBOOK.md`](../RUNBOOK.md)

---

## 1. Vertex — where vibration / placement lives

**File:** `native/samples/VernacularViewport/lessons/temple_vs.slang`  
**Entry:** `vsMain` (included by `VernacularViewport.3d.slang`)

Vertex shader owns **where the mesh sits** after the scene transform:

- Vibration Modes (`F3`): standing-wave displacement on lattice cubes (`gVertexWaves` / `gVibeAmp`).
- Temple ocean: flatten the water grid to the deck so the **pixel** shader can raymarch beauty.

Edit VS in **F8** → **Ctrl+S** writes repo + runtime shaders → GPU reload (or **F5**).

---

## 2. Pixel — looks + lighting modes

**File:** `native/samples/VernacularViewport/lessons/temple_ps.slang`  
**Looks:** `lessons/shading_ladder.slang` · **Env:** `lessons/temple_env.slang`

Pixel shader owns **what you see**:

- Chapter bank `[` `]` (UV → Physical → paint → school ports).
- Lighting modes **L** — Unlit / Lambert / Blinn / Physical — same `getSunDirection()` as sky / ocean.
- Sky / ocean raymarch / land / canvas rim + fog.

Analytic raster only (no `alphaTest` / material-eval link traps).

---

## 3. Compute — boids / fields

**Files:** `lessons/boids.cs.slang` (dispatch) · `lessons/boids.3d.slang` (impostor quads)

Toggle **B** or F1 → **Boids (compute flock)**.

Each frame: compute updates a structured buffer (separation / alignment / cohesion). A tiny raster pass draws camera-facing quads — **not** Scene.Raster, so the analytic temple path stays healthy.

Research engines put agents, particles, and fields on **CS** because the neighborhood loop is not a triangle.

---

## 4. Differential — train / fit style

**File:** `lessons/temple_diff.slang` (2D live `hello_pixel`)  
**Sisters:** [`../../labs/diffslang/d01_differentiable_attr.slang`](../../labs/diffslang/shaders/d01_differentiable_attr.slang) · [`../../labs/slang_playground/sp08_autodiff.slang`](../../labs/slang_playground/shaders/sp08_autodiff.slang) · neural N03

The F8 **Diff** tab shows this module marked **not in 3D PSO**. **Falcor 3D raster does not run `bwd_diff` this pass** — train/fit stays in 2D live / labs CLIs (`train_brdf`, slangpy). That is honest: autodiff is a compiler feature you compose, not a checkbox on the swapchain.

---

## 5. Upscale — DLSS / TAA / internal scale

**F1 → Upscale** (or **U**): Off / Internal scale / TAA / DLSS (greyed).

| Rung | What runs | How |
|------|-----------|-----|
| **Off** | Native swapchain | Same as Iteration 6 |
| **Internal scale** | 0.50 / 0.67 / 1.0 + bilinear or bicubic blit | Always available. Render low, reconstruct high. |
| **TAA** | Falcor-style neighborhood clamp + history | Depth → screen mvec (`lessons/mvec.ps.slang`) + `lessons/taa.ps.slang` |
| **DLSS** | **Not in SampleApp this pass** | `DLSSPass.dll` + `nvngx_dlss.dll` **are** in `bin/Release`. Falcor `DLSSPass` is a **Mogwai render-graph plugin**: color + depth + mvec + camera jitter + `NGXWrapper` (plugin-private). SampleApp has no `RenderData`. Use Mogwai `PathTracer` + `DLSSPass` — **don't rewrite UNIX / NGX**. |

NIS / FSR are not first-class Falcor 8.0 passes here. NRD is a path-tracer denoiser, not a cheap upscaler.

---

## Open the in-app editor

**F8** (or F1 **Slang editor**) — ImGui panel in `VernacularViewport.exe`: **VS / PS / CS / Diff**. Loads the Slang Falcor compiled under `shaders/Samples/VernacularViewport/`. **Ctrl+S** saves repo + runtime then reloads. **E** stays Fly-up. **Not** `python -m slang_falcon.live`.

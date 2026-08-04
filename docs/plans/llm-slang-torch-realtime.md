# Plan: Inline LLM / AI + SlangPy / SlangTorch realtime

**Pinned on:** [docs/roadmap.md](../roadmap.md)  
**Status:** planning only — no feature implementation in this doc’s scope  
**Goal:** Link host-side LLM assistance and PyTorch training/export with the Slang + SlangPy playground so neural shading can run in (near) real time beside the live preview.

---

## Context (what exists today)

| Piece | Role today |
|-------|------------|
| `python -m slang_falcon.live` | Desktop pygame window: edit `.slang` → save → GPU recompile + preview |
| `slangpy.Tensor` | Device tensors for MLP weights/grads (`network.py`, train/infer CLIs) |
| `train_brdf` / `infer` | In-shader Disney BRDF MLP train + compare strip (Slang autodiff via SlangPy; numpy fallback) |
| Weight format | `SFMLP001` binary (`docs/weight_format.md`) for Falcor / WebGPU later |
| Phase 2 (roadmap) | Falcor + Vulkan CoopVec host on RTX |
| LLM / slangtorch | **Not wired yet** — this plan defines how they land |

Teaching story stays: **teacher → small MLP in shaders → inference in-shader**, not hand-authoring every lighting approximation. LLMs help *author* shaders and glue; they do not replace the MLP path.

---

## Hardware & runtime defaults

| Concern | Recommendation (v0 default) | Alternatives (keep optional) |
|---------|------------------------------|------------------------------|
| Neural shading math | GPU via SlangPy (D3D12/Vulkan/…); later **CoopVec / Tensor Cores** on RTX for Phase 2+ | Scalar / float MLP fallback for debug and non-NV |
| Training / tensor glue | **PyTorch** (+ SlangPy tensors; optional `slangtorch` where it fits) | Pure SlangPy autodiff path we already ship |
| LLM for authoring | **Local small model** (Ollama / similar) — privacy, offline playground | Cloud API (OpenAI-compatible, etc.) behind an explicit opt-in |
| Live preview | Always local GPU frame path; never wait on cloud LLM | Async assist only |

**Why these defaults:** playground users edit shaders on their machine; a local LLM avoids shipping code to a vendor by default. Torch is the ecosystem standard for small-MLP experiments and export; CoopVec is the NVIDIA neural-shading acceleration path already targeted by Phase 2 / RTXNS patterns.

---

## Non-goals (v0)

- Do **not** train or run a full LLM *inside* Slang / as a shader.
- Do **not** block the live preview on cloud round-trips or LLM latency.
- Do **not** require an API key for basic live edit + BRDF MLP train/infer.
- Do **not** replace the existing Slang autodiff train path with a Torch-only story in one leap — bridge first, then dual-path.
- Do **not** claim CoopVec / Tensor-Core speedups on WebGPU (Phase 3 remains float MLP).
- Do **not** expand scope to audio-shader LLM assist until the image path is proven (see audio item on the main roadmap).

---

## Phase A — SlangPy ↔ PyTorch bridge (foundation)

**Intent:** Make tensor and weight interchange with Torch explicit and tested, without changing the live UI.

### Deliverables

1. **Interop helpers** (package-internal first):
   - `slangpy.Tensor` ↔ `numpy` ↔ `torch.Tensor` (CPU and, where device sharing is practical, GPU).
   - Load/save `SFMLP001` from Torch `state_dict` / `nn.Module` matching `BRDF_LAYER_SIZES`.
2. **Optional extra** `.[torch]` (or similar) so base install stays lean; document CUDA vs CPU Torch.
3. **Spike doc** on `slangtorch` vs “Torch for training + SlangPy for in-shader forward”: pick one primary training story for the labs; keep the other as advanced.
4. **Tests:** round-trip weights (Torch → bin → SlangPy infer strip matches within tolerance).

### Exit criteria

- A developer can train a tiny BRDF MLP in Torch *or* keep SlangPy training, export the same binary, and run `slang_falcon.infer` unchanged.
- No live-window or LLM work required yet.

### Depends on

- Existing `network.py`, `weights.py`, `train_brdf` / `infer`.

---

## Phase B — Inline “AI assist” in the live window

**Intent:** Host-side LLM suggests or edits shader snippets (`hello_pixel`, lab kernels) while the preview keeps running on the last good compile.

### Deliverables

1. **UI surface** in the live mini-IDE: prompt box / command (e.g. “suggest edit for current buffer”) — not in-shader.
2. **Provider abstraction:**
   - Default: local (Ollama HTTP) with a pinned small coding-capable model.
   - Optional: env-configured API endpoint + key.
3. **Safe apply path:** LLM returns a patch or full buffer → user accepts → write file → existing hot-reload compiles. Reject/diff view preferred over silent overwrite.
4. **Context pack:** current file, entry name, last compiler error log (from the green console), short lab instructions — keep prompts small.
5. **Non-blocking:** LLM calls on a background thread/async; preview and F11 / wobble / reload stay responsive. On failure, show console message only.

### Exit criteria

- From the live window, a user can prompt → get a suggestion → accept → see the preview update via normal save/reload.
- Preview never freezes waiting on the model.

### Depends on

- Stable live editor + console (already shipped).
- No hard dependency on Phase A (assist is text-only), but shared config UX can land together.

---

## Phase C — Small neural nets in-shader (BRDF MLP) + live preview

**Intent:** Close the loop: train/export via Torch and/or SlangPy, then **inference in the live preview** (not only CLI compare PNG).

### Deliverables

1. **Live mode / lab flag:** load `assets/weights/brdf_mlp.bin` (or hot-reload weights on file change) into SlangPy tensors; dispatch existing (or thin wrapper) infer entry each frame.
2. **Optional side-by-side:** teacher | MLP | abs-diff in the preview (mirror CLI strip).
3. **Torch training recipe** in labs that writes the same weight file the live path consumes (Phase A helpers).
4. **Docs:** Lab N “train once, see live” — explicit that this is *shading* MLP inference, not LLM tokens in the shader.

### Exit criteria

- After `train_brdf` (or Torch export), opening live with the BRDF entry shows neural shading updating every frame without re-exporting from an LLM.
- Weight file change can refresh inference without restarting the process (best-effort).

### Depends on

- Phase A weight bridge (Torch path).
- Current `train_brdf.slang` / `BrdfNetwork` stack.

---

## Phase D — Real-time inference loop

**Intent:** Production-shaped loop: per-frame neural results feed shader uniforms/textures; authoring LLM remains optional and asynchronous.

### Deliverables

1. **Frame loop contract:**
   - Path 1: **In-shader MLP** (SlangPy now; CoopVec in Falcor Phase 2) — preferred for shading.
   - Path 2: **Host Torch forward** → upload texture/buffer each frame — for prototypes larger than the in-shader net or debugging.
2. **Uniform/texture binding** helpers so labs don’t hand-roll RHI each time.
3. **CoopVec / Tensor Core note:** when native host lands, same `SFMLP001` weights; document RTX 20xx+ / `VK_NV_cooperative_vector` requirements (align with README hardware table).
4. **Optional dual cockpit:** local LLM assist (Phase B) while GPU neural shading (Phase C/D) runs — clearly separated threads and failure domains.
5. **Perf budget:** target interactive rates for the small BRDF net at lab resolutions (e.g. 512²); document when to drop to smaller net or CoopVec.

### Exit criteria

- Documented, demable loop: edit shader and/or tweak weights → continuous preview; LLM assist never on the critical path.
- Clear choice matrix: “use in-shader / CoopVec for shading; use Torch host upload only when needed; use local LLM only for authoring.”

### Depends on

- Phases A–C for Python playground.
- Phase 2 native Falcor work for CoopVec parity (can track in parallel; not a v0 blocker for SlangPy realtime).

---

## Suggested sequencing

```
Phase A (bridge + tests)
    │
    ├─► Phase B (live AI assist)     ← can parallelize after A starts
    │
    └─► Phase C (MLP in live preview)
            │
            └─► Phase D (frame loop + optional CoopVec / Torch upload)
```

Ship teaching value early: **A → C** keeps the neural-shading curriculum honest; **B** is the “playground IDE” enhancer and must stay off the render critical path.

---

## Open questions (resolve during Phase A/B spikes)

1. First-class `slangtorch` vs Torch-only export into SlangPy — which lab text endorses?
2. Default Ollama model tag and minimum VRAM guidance alongside GPU shading.
3. Whether weight hot-reload should share the same file watcher as `.slang` or a dedicated `--weights` watch.
4. How much Falcor Phase 2 must exist before advertising “CoopVec realtime” vs “SlangPy realtime.”

---

## Success metric (overall)

A student can: train a tiny BRDF MLP (SlangPy or Torch), see it in the live window at interactive rates, and optionally ask a **local** LLM to help edit `hello_pixel` / lab shaders — without ever putting an LLM in the shader or stalling the preview on the network.

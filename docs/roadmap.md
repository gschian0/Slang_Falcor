# Roadmap

## Pinned: VERNACULAR (KodeLife-class Slang IDE)

**Status:** V0 branding live — product face **VERNACULAR**; package `slang_falcon`; CLI alias `vernacular`. Round 1: [ROUND1.md](ROUND1.md).

Productize the live playground as **VERNACULAR**: KodeLife-class live shader IDE for technical artists on the open Slang/neural stack ([manifesto](manifesto.md)), with a built-in AI helper (local small model + Slang docs MCP). Package stays `slang_falcon` (folder rename `Slang_Falcon` is manual later).

| Phase | Focus |
|-------|--------|
| V0 | Branding face (title / docs / optional thin CLI alias) — no package break |
| V1 | IDE parity: project save, multi-buffer, uniform panel; audio-reactive pinned |
| V2 | Side-chat AI helper (Ollama default; patch buffer; cite docs; never block preview) |
| V3 | Falcor 3D viewport ([falcor-viewport-sam](plans/falcor-viewport-sam.md)) |

**Full plan:** [plans/vernacular.md](plans/vernacular.md)

---

## Pinned: Companion parable (school text)

**Status:** docs — teaching allegory, not a product phase

[How to have robots steal coffee from Babylon on their own](companion/robots_steal_coffee_from_babylon.md) — manifesto-aligned story + curriculum track (Babylon = closed stacks; robot = open pipeline; 2026: coffee → Yerba Matte / French Press = closed vocabulary → open vernacular). Links: [manifesto](manifesto.md) · [VERNACULAR](plans/vernacular.md).

---

## Pinned: Inline LLM / AI + SlangTorch realtime

**Status:** planned (docs only — not implemented yet)

Bridge host-side LLMs and PyTorch with the existing SlangPy live playground and in-shader MLP path, toward real-time neural inference beside the live preview.

| Phase | Focus |
|-------|--------|
| A | SlangPy ↔ PyTorch bridge (tensors / export we already lean on) |
| B | Inline “AI assist” in the live window (host LLM edits shaders) |
| C | Small nets in-shader (BRDF MLP) via Torch/SlangPy → live preview |
| D | Real-time inference loop (Torch or CoopVec → uniforms/textures/frame) |

**Defaults:** local small LLM (e.g. Ollama) for playground privacy; PyTorch for training/export. Hardware: RTX Tensor Cores / CoopVec for neural shading when available.

**Full plan:** [plans/llm-slang-torch-realtime.md](plans/llm-slang-torch-realtime.md)

---

## Pinned: Falcor viewport + Segment Anything

**Status:** Phase 0 **in progress** (fetch script + build docs + scaffold) — not a full 3D viewport yet

Hoist Slang into a **Falcor** 3D host (meshes, experimental passes, viewport settings) with **inline viewport AI**. First AI feature: **Segment Anything** via **2D SAM2 on the viewport color buffer**, then lift masks with depth/camera (true 3D SAM later). Builds on existing [`native/`](../native/README.md) scaffold; Phase 4 AI panel ties to the LLM plan above.

| Phase | Focus |
|-------|--------|
| 0 | Wire Falcor host — fetch Falcor, minimal mesh scene, Slang material / neural pass |
| 1 | Viewport capture (color + depth) + camera matrices export |
| 2 | Host-side SAM2 (local, async) — point/box prompts, mask overlay |
| 3 | Lift 2D mask → 3D selection (depth unproject / mesh pick) |
| 4 | Inline AI panel (viewport-aware prompts; shared with LLM plan) |
| 5 | Experimental Slang neural passes on selected region |

**Defaults:** 2D SAM2 + depth lift first; local Torch/CUDA on RTX; async only (never stall the frame). Falcor fetched at build time, not vendored.

**Full plan:** [plans/falcor-viewport-sam.md](plans/falcor-viewport-sam.md)

---

## Pinned: Live playground polish

**Status:** **chrome pinned / good enough** — dual fullscreen (window + shader-only), shaped wobble, two-square layout, curriculum keys ship. Optional: in-window lesson browser / prev-next buttons. **Focus moves to Falcor Phase 0** (see above).

**Known issue:** shader-only FS (**F10** / cyan) can **black out** the display — prefer **window FS (F11)**; fix later (borderless windowed, never exclusive). See [ROUND1.md](ROUND1.md).

**Full plan:** [plans/live-playground-polish.md](plans/live-playground-polish.md)

---

## Pinned: Vsynth-style feedback patches

**Status:** planned (docs + optional F0 stub — no live ping-pong host yet)

Video feedback / patch graphs for VERNACULAR: Slang kernels as nodes, textures as edges, classic ping-pong feedback, multi-pass networks with delay taps, and **differentiable diffusion as trainable feedback** (warp/diffusion params vs target). Aligns with vernacular multi-pass gap and manifesto open-stack stance (learn from Notch/Vsynth craft; ship readable Slang + JSON).

| Phase | Focus |
|-------|--------|
| F0 | Single ping-pong feedback lesson (needs small live A/B buffer bind; stub simulates trails today) |
| F1 | Patch JSON graph runner |
| F2 | Diffusable / trainable feedback (Slang `[Differentiable]` + SlangPy) |
| F3 | Video I/O + audio-reactive (later) |
| F4 | Falcor multi-pass when 3D host exists |

**Full plan:** [plans/vsynth-feedback.md](plans/vsynth-feedback.md) · stub: [`labs/feedback/`](../labs/feedback/)

---

## Audio shaders (future)

Today’s live hot-reload is **image/compute pixels** via SlangPy (`python -m slang_falcon.live`).

**Future:** audio shaders — Slang compute kernels that write PCM/sample buffers, then live-reload and play through a host audio callback (sounddevice/etc.). Same paradigm: edit `.slang` → save → hear the update. Optional neural / tiny-MLP for timbre later.

Not WebAudio parity in Phase 3 yet; native CoopVec audio is speculative.

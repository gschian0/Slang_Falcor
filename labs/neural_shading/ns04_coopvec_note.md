# NS04 — Cooperative vectors (Phase 2 note)

**Job:** know where Tensor-Core acceleration fits — and that Phase 1 live demos stay scalar.

**Source post:** [How to Get Started with Neural Shading](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/) (cooperative vectors section)

## Run

```powershell
python -m slang_falcon.live --lesson neural_shading/ns04_coopvec_note
```

Schematic: input vector × weight matrix → output, with a pulse suggesting cooperative execution. **Not** a real `CoopVec` / `coopVecMatMulAdd` dispatch.

## Idea

| Phase | What you get |
|-------|----------------|
| 1 (this playground) | SlangPy + scalar / Tensor MLP train & live `hello_pixel` |
| 2 (`native/`) | Falcor / Vulkan host + `VK_NV_cooperative_vector` for inline inference |
| 3 (`web/`) | WebGPU float MLP — no Tensor-Core claim |

CoopVec lets you write normal mat–vec code; the compiler maps it to Tensor Cores when the hardware and API allow it. Patterns: [RTXNS](https://github.com/NVIDIA-RTX/RTXNS), roadmap in root `README.md`.

## Next

`neural_shading/ns05_slangpy_train_loop` · then afternoon track.

Shader: `shaders/ns04_coopvec_note.slang`.

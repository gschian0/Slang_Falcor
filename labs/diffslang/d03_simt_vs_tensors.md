# D03 — SIMT pixels vs tensor batches

**Job:** keep both mental models — graphics threads and ML batches — without fighting either.

**Source post:** [Differentiable Slang](https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/) (graphics ↔ ML bridge, Falcor reuse, SlangPy/PyTorch)

## Run

```powershell
python -m slang_falcon.live --lesson diffslang/d03_simt_vs_tensors
```

- **Left:** classic per-pixel shade (SIMT “one thread, one UV”)
- **Right:** same shade with a batch lattice overlay — how ML people picture many samples at once

## Idea

Differentiable Slang keeps **shader** structure (interfaces, pipelines, SIMT) while exposing derivatives that ML stacks expect as **tensors**. You do not rewrite the renderer as a giant NumPy graph; you mark the math `[Differentiable]` and let the compiler generate the backward.

| Graphics habit | ML habit | Slang bridge |
|----------------|----------|--------------|
| `hello_pixel(pixel, res)` | batched `(N, …)` tensors | same kernel; SlangPy `grid` / Tensor |
| Falcor / RHI passes | PyTorch / optimizers | SlangPy device + `.bwds` |
| hand GLSL lighting | train MLP approx | Lab 4 / neural_shading track |

## Try

1. Edit `shade` — both sides stay in sync (same function).
2. Compare to `neural/n03_autodiff_intuition` (loss viz) and Lab 4 (real Tensor train).

## Next

Neural shading get-started: `neural_shading/ns01_trainable_pipeline` · hub `labs/neural_trilogy/README.md`

Shader: `shaders/d03_simt_vs_tensors.slang`.

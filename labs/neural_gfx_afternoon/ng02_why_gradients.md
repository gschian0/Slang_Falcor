# NG02 — Why gradients

**Job:** see target | random blobs | per-pixel L2 — the afternoon’s “we need derivatives” moment.

**Source post:** [Neural Graphics in an Afternoon](https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/)

## Run

```powershell
python -m slang_falcon.live --lesson neural_gfx_afternoon/ng02_why_gradients
```

Without autodiff you’d hand-write ∂loss/∂(center, σ, color) for every splat. Slang’s `[Differentiable]` + `bwd_diff` / `.bwds` removes that chore.

## Next

`neural_gfx_afternoon/ng03_gaussian_fit` · real train: `python -m slang_falcon.fit_blobs`

Shader: `shaders/ng02_why_gradients.slang`.

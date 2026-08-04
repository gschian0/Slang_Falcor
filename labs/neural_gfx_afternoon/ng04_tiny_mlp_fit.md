# NG04 — Tiny MLP texture fit

**Job:** afternoon closing beat — UV→RGB net morphs toward a procedural texture.

**Source post:** [Neural Graphics in an Afternoon](https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/) (after splats: same autodiff stack trains networks)

## Run

```powershell
python -m slang_falcon.live --lesson neural_gfx_afternoon/ng04_tiny_mlp_fit
```

Left: target. Right: frequency-encoded `4→6→3`-style demo whose weights lerp bad→better with `time`.

For a serious MLP teacher match use Lab 4 / `neural_shading/ns02_mlp_approx_shader`.

## Afternoon checklist

1. Call Slang from Python (NG01)
2. Define loss vs target (NG02)
3. Optimize splat params (NG03 + `fit_blobs`)
4. Same stack → tiny MLP (NG04)

Hub: `labs/neural_trilogy/README.md`

Shader: `shaders/ng04_tiny_mlp_fit.slang`.

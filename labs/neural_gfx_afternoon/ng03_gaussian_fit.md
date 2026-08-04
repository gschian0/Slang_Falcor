# NG03 — Gaussian image fit

**Job:** watch 2D Gaussians morph from a bad init toward a two-blob target (afternoon splat story).

**Source post:** [Neural Graphics in an Afternoon](https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/)

## Run (live morph)

```powershell
python -m slang_falcon.live --lesson neural_gfx_afternoon/ng03_gaussian_fit
```

Left: target. Right: blobs; bottom bar = fake “iteration” progress (`time` → 8s).

## Run (real Adam fit)

```powershell
python -m slang_falcon.fit_blobs --steps 400 --blobs 8 --out assets/output/fit_blobs.png
```

CPU NumPy Adam over isotropic Gaussians + L2 to a procedural target — same *loop shape* as the blog (forward → loss → grads → Adam), tiny enough for a smoke-friendly CLI.

## Next

`neural_gfx_afternoon/ng04_tiny_mlp_fit`

Shader: `shaders/ng03_gaussian_fit.slang`.

# sp07_gsplat2d_diff — Differentiable 2D Splatter

Target | fitting blobs | abs-error strip.

**Source:** [Slang Playground](https://shader-slang.org/slang-playground/) · demos in [shader-slang/slang-playground](https://github.com/shader-slang/slang-playground) (`public/demos/`).
**Attribution:** shader-slang (Apache-2.0 WITH LLVM-exception). Ported for Slang_Falcon live preview — not a fork of the playground UI.

## Run

```powershell
python -m slang_falcon.live --lesson slang_playground/sp07_gsplat2d_diff
python -m slang_falcon.live --lesson slang_playground/sp07_gsplat2d_diff --once
```

## Try

1. Open the matching demo in the [playground](https://shader-slang.org/slang-playground/) and compare.
2. Edit `shaders/sp07_gsplat2d_diff.slang` — save to hot-reload.
3. Note API differences: playground uses `import rendering` / `drawPixel`; we use `hello_pixel(pixel, resolution, time)`.

Shader: `shaders/sp07_gsplat2d_diff.slang`

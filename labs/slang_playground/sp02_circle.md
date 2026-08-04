# sp02_circle — ShaderToy: Circle

Polar color beams (ShaderToy XdlSDs).

**Source:** [Slang Playground](https://shader-slang.org/slang-playground/) · demos in [shader-slang/slang-playground](https://github.com/shader-slang/slang-playground) (`public/demos/`).
**Attribution:** shader-slang (Apache-2.0 WITH LLVM-exception). Ported for Slang_Falcon live preview — not a fork of the playground UI.

## Run

```powershell
python -m slang_falcon.live --lesson slang_playground/sp02_circle
python -m slang_falcon.live --lesson slang_playground/sp02_circle --once
```

## Try

1. Open the matching demo in the [playground](https://shader-slang.org/slang-playground/) and compare.
2. Edit `shaders/sp02_circle.slang` — save to hot-reload.
3. Note API differences: playground uses `import rendering` / `drawPixel`; we use `hello_pixel(pixel, resolution, time)`.
4. Beams use **2×2 supersample** in-shader for smoother edges.

Shader: `shaders/sp02_circle.slang`

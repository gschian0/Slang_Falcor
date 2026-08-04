# sp05_multi_kernel — Multi-kernel

Sine buffer visualized as grayscale (one-entry stand-in).

**Source:** [Slang Playground](https://shader-slang.org/slang-playground/) · demos in [shader-slang/slang-playground](https://github.com/shader-slang/slang-playground) (`public/demos/`).
**Attribution:** shader-slang (Apache-2.0 WITH LLVM-exception). Ported for Slang_Falcon live preview — not a fork of the playground UI.

## Run

```powershell
python -m slang_falcon.live --lesson slang_playground/sp05_multi_kernel
python -m slang_falcon.live --lesson slang_playground/sp05_multi_kernel --once
```

## Try

1. Open the matching demo in the [playground](https://shader-slang.org/slang-playground/) and compare.
2. Edit `shaders/sp05_multi_kernel.slang` — save to hot-reload.
3. Note API differences: playground uses `import rendering` / `drawPixel`; we use `hello_pixel(pixel, resolution, time)`.

Shader: `shaders/sp05_multi_kernel.slang`

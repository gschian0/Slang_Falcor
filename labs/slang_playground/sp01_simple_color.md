# sp01_simple_color — Simple Color

Solid flat color — first playground kernel (upstream called this “Simple Image”).

**Source:** [Slang Playground](https://shader-slang.org/slang-playground/) · demos in [shader-slang/slang-playground](https://github.com/shader-slang/slang-playground) (`public/demos/`).
**Attribution:** shader-slang (Apache-2.0 WITH LLVM-exception). Ported for Slang_Falcon live preview — not a fork of the playground UI.

## Run

```powershell
python -m slang_falcon.live --lesson slang_playground/sp01_simple_color
python -m slang_falcon.live --lesson slang_playground/sp01_simple_color --once
```

## Try

1. Use the **Color** panel (swatch / HSV / RGB) — entry takes `float3 color`. Hover `float3` or `color` in the editor to focus the picker.
2. Open the matching demo in the [playground](https://shader-slang.org/slang-playground/) and compare.
3. Edit `shaders/sp01_simple_color.slang` — save to hot-reload.
4. Next lesson **Simple Image** samples a real texture (`sp16_simple_image`).

Shader: `shaders/sp01_simple_color.slang`

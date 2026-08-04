# sp16_simple_image — Simple Image

Sample a real photo (`cowboy_hat.png`) via `Texture2D` + `SamplerState`. UV comes from `pixel / resolution`; optional `float3 tint` multiplies RGB.

Asset: `labs/slang_playground/assets/cowboy_hat.png`

## Run

```powershell
python -m slang_falcon.live --lesson slang_playground/sp16_simple_image
python -m slang_falcon.live --lesson slang_playground/sp16_simple_image --once
```

## Try

1. Confirm the cowboy-hat photo fills the viewport (letterboxed by the live window, not the shader).
2. Use the **Color** panel on `tint` (hover `float3` / `tint` in the editor) — white = identity, other values multiply the image.
3. Edit UV math or drop the V flip — save to hot-reload.
4. Compare with **Simple Color** (`sp01_simple_color`) which only returns a solid `float3`.

Shader: `shaders/sp16_simple_image.slang`

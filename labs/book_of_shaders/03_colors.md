# 03 — Colors

**Job:** mix two colors across UV — gradients you control.

Read: [Colors](https://thebookofshaders.com/06/)

## Run

```powershell
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/03_colors.slang --entry hello_pixel
```

## Try

1. Use the **Color** panel swatches for `color_a` / `color_b` (HSV square + RGB sliders).
2. Mix on `uv.y` instead of `uv.x`.
3. Nest a second `lerp` for a three-stop gradient.

Shader: `shaders/03_colors.slang`.

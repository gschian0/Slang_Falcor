# sp14_image_from_url — Image From URL

Aspect-correct sample of a **cool shades smiley** (cyber / shader-playground vibe) — stand-in for a URL-loaded texture.

**Source:** [Slang Playground](https://shader-slang.org/slang-playground/) · demos in [shader-slang/slang-playground](https://github.com/shader-slang/slang-playground) (`public/demos/`).
**Attribution:** shader-slang (Apache-2.0 WITH LLVM-exception). Ported for Slang_Falcon live preview — not a fork of the playground UI.

Upstream playground binds `Texture2D` from a URL (`jeep.jpg`). Live `hello_pixel` has no URL binder, so this lesson draws a procedural cool-shades smiley with the same UV flip / aspect idea. Local fallback art: `assets/images/cool_shades_smiley.png`.

## Run

```powershell
python -m slang_falcon.live --lesson slang_playground/sp14_image_from_url
python -m slang_falcon.live --lesson slang_playground/sp14_image_from_url --once
```

## Try

1. Open the matching demo in the [playground](https://shader-slang.org/slang-playground/) and compare (URL texture vs our procedural stand-in).
2. Edit `shaders/sp14_image_from_url.slang` — save to hot-reload. Tweak lens colors, smile, or neon grid.
3. Note API differences: playground uses `import rendering` / `drawPixel` + `[playground::URL(...)]`; we use `hello_pixel(pixel, resolution)`.

Shader: `shaders/sp14_image_from_url.slang`

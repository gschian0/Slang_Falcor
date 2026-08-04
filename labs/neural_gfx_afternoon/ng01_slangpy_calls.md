# NG01 — Call Slang from Python

**Job:** start the afternoon the same way the blog does — one Slang entry, no API soup.

**Source post:** [Neural Graphics in an Afternoon](https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/)

## Run

```powershell
python -m slang_falcon.live --lesson neural_gfx_afternoon/ng01_slangpy_calls
```

Grid overlay = “each pixel is a dispatch cell” — the same idea as SlangPy `spy.grid(shape=(W,H))`.

## Idea

SlangPy loads a `.slang` module and calls functions like ordinary Python. Live preview is exactly that path: `hello_pixel(pixel, resolution[, time])` → RGB tensor → window.

## Next

`neural_gfx_afternoon/ng02_why_gradients`

Shader: `shaders/ng01_slangpy_calls.slang`.

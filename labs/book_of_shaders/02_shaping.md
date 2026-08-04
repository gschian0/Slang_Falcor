# 02 — Shaping functions

**Job:** plot a 1D curve `y = f(x)` across the image.

Read: [Shaping functions](https://thebookofshaders.com/05/)

## Run

```powershell
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/02_shaping.slang --entry hello_pixel
```

## Try

1. Swap `pow(st.x, 3.0f)` for `smoothstep(0.1f, 0.9f, st.x)`.
2. Widen the green stroke: change `0.02f` in `plot`.
3. Stack two curves (two `plot` calls, two colors).

Shader: `shaders/02_shaping.slang`.

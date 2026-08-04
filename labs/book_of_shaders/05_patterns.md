# 05 — Patterns

**Job:** tile space with `floor` / `frac` and repeat one shape.

Read: [Patterns](https://thebookofshaders.com/09/)

## Run

```powershell
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/05_patterns.slang --entry hello_pixel
```

## Try

1. Change `scale` (more / fewer tiles).
2. Replace the circle with a small box per cell.
3. Kill the time wobble — set `r` to a constant.

Shader: `shaders/05_patterns.slang` → uses `time` for a gentle radius pulse.

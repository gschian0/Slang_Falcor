# 04 — Shapes

**Job:** draw a circle and a box with signed-distance style edges.

Read: [Shapes](https://thebookofshaders.com/07/)

## Run

```powershell
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/04_shapes.slang --entry hello_pixel
```

## Try

1. Move the circle: change the offset in `p - float2(...)`.
2. Grow the box half-extents.
3. Soften edges: bump the `soft` argument to `fill`.

Shader: `shaders/04_shapes.slang`.

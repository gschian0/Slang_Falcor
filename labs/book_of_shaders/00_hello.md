# 00 — Hello pixel

**Job:** get a color on screen from UV. Nothing else.

Read: [Getting started](https://thebookofshaders.com/00/) · [Hello World](https://thebookofshaders.com/01/)  
*(Original narrative lives there — this lab is a Slang workout.)*

## Run

```powershell
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/00_hello.slang --entry hello_pixel
```

## Try

1. Return a solid color: `float3(1.0f, 0.2f, 0.1f)`.
2. Swap `uv.x` / `uv.y`.
3. Multiply a channel by `0.5f` — watch the gradient flatten.

Shader: `shaders/00_hello.slang` → `hello_pixel(pixel, resolution)`.

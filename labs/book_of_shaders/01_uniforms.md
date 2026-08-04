# 01 — Uniforms (time)

**Job:** make the frame breathe using `time` from live.

Read: [Uniforms](https://thebookofshaders.com/03/)

Live injects `float time` = seconds since the preview started when your entry declares that parameter.

## Run

```powershell
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/01_uniforms.slang --entry hello_pixel
```

Smoke at a fixed clock:

```powershell
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/01_uniforms.slang --entry hello_pixel --once --time 1.25
```

## Try

1. Change `time * 2.0f` → faster / slower pulse.
2. Drive only the red channel with `pulse`; leave green/blue from UV.
3. Use `abs(sin(time))` for a different envelope.

Shader: `shaders/01_uniforms.slang` → `hello_pixel(pixel, resolution, time)`.

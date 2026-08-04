# Book of Shaders → Slang (BOOM track)

Classic fragment-shader playground ideas, ported to **Slang** and live-reloaded with SlangPy.

> Inspired by [The Book of Shaders](https://thebookofshaders.com/) (Patricio Gonzalez Vivo & Jen Lowe).  
> This track is an **original** Slang progression — not a copy of the book’s prose.  
> Read the original chapters for the full narrative; edit these kernels to feel the math.

## Run it (live)

From the repo root (venv activated, `pip install -e .`):

```powershell
# Curriculum (preferred) — start at 00, press ] to advance
python -m slang_falcon.live --lesson bos/00_hello
python -m slang_falcon.live --lesson 0

# Or by path
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/00_hello.slang --entry hello_pixel
python -m slang_falcon.live --shader labs/book_of_shaders/shaders/01_uniforms.slang --entry hello_pixel

# Headless smoke
python -m slang_falcon.live --lesson bos/00_hello --once
python -m slang_falcon.live --lesson bos/02_shaping --once --out assets/output/bos_02.png
```

Edit in the side panel → save / debounce → window updates. Esc quits.  
With the editor unfocused: **]** / Right = next lesson, **[** / Left = previous, **L** = list.

After chapter 05, **]** continues into **Slang Playground** ports (`slang_playground/sp01`…), then the neural track (`neural/n01`…).

**Entry contract:** every lab exposes `hello_pixel`. Animated chapters add `float time` (seconds since live start). Kernels without `time` (including `slang/lab_kernels.slang`) keep working.

## Chapters

| # | Lab | Shader | Book chapter (read) |
|---|-----|--------|---------------------|
| 00 | [Hello](00_hello.md) | `shaders/00_hello.slang` | [Getting started](https://thebookofshaders.com/00/) / [Hello World](https://thebookofshaders.com/01/) |
| 01 | [Uniforms / time](01_uniforms.md) | `shaders/01_uniforms.slang` | [Uniforms](https://thebookofshaders.com/03/) |
| 02 | [Shaping functions](02_shaping.md) | `shaders/02_shaping.slang` | [Shaping functions](https://thebookofshaders.com/05/) |
| 03 | [Colors](03_colors.md) | `shaders/03_colors.slang` | [Colors](https://thebookofshaders.com/06/) |
| 04 | [Shapes](04_shapes.md) | `shaders/04_shapes.slang` | [Shapes](https://thebookofshaders.com/07/) |
| 05 | [Patterns](05_patterns.md) | `shaders/05_patterns.slang` | [Patterns](https://thebookofshaders.com/09/) |

One job per lab. Nail these, then branch into more Book chapters yourself.

## Why this exists

The main `labs/` track teaches **neural shading** (teacher → MLP → infer).  
This side track teaches **pixel math fluency** in the same live loop — so when you write loss kernels and viz shaders later, UV / mix / SDF aren’t the hard part.

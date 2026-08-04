# Slang Playground → live lessons

Ports of the public demos from the official **[Slang Playground](https://shader-slang.org/slang-playground/)** into Slang_Falcon’s `hello_pixel` live loop.

| | |
|--|--|
| Upstream demos | [`public/demos/`](https://github.com/shader-slang/slang-playground/tree/main/public/demos) in [shader-slang/slang-playground](https://github.com/shader-slang/slang-playground) |
| License | Apache-2.0 WITH LLVM-exception (shader-slang) |
| Adaptation | `import rendering` / `drawPixel` / multi-kernel WebGPU → `hello_pixel(int2, int2[, float time])` |

Educational intent is preserved; APIs that need playground host features (URL textures, mouse paint canvas, groupshared tile sort, in-shader Adam) are **simplified** so they still run under `python -m slang_falcon.live`.

**Not ported as live image lessons:** Simple Print (text-only), Graphics Entrypoints (VS/FS compile-only), Atomics (print-only atomic API tour). Open those in the playground.

## Curriculum order

Phase `slang_playground` sits **after Book of Shaders** and **before neural bridges** in `labs/curriculum.json`.

```powershell
python -m slang_falcon.lessons
python -m slang_falcon.live --lesson slang_playground/sp01_simple_color
# From BoS 05, press ] to enter this phase
```

## Lessons

| Id | Title | Run |
|----|-------|-----|
| `slang_playground/sp01_simple_color` | Simple Color | `python -m slang_falcon.live --lesson slang_playground/sp01_simple_color` |
| `slang_playground/sp16_simple_image` | Simple Image | `python -m slang_falcon.live --lesson slang_playground/sp16_simple_image` |
| `slang_playground/sp02_circle` | ShaderToy: Circle | `python -m slang_falcon.live --lesson slang_playground/sp02_circle` |
| `slang_playground/sp03_ocean` | ShaderToy: Ocean | `python -m slang_falcon.live --lesson slang_playground/sp03_ocean` |
| `slang_playground/sp04_volume_slice` | Volume Slice | `python -m slang_falcon.live --lesson slang_playground/sp04_volume_slice` |
| `slang_playground/sp05_multi_kernel` | Multi-kernel | `python -m slang_falcon.live --lesson slang_playground/sp05_multi_kernel` |
| `slang_playground/sp06_gsplat2d` | 2D Splatter | `python -m slang_falcon.live --lesson slang_playground/sp06_gsplat2d` |
| `slang_playground/sp07_gsplat2d_diff` | Differentiable 2D Splatter | `python -m slang_falcon.live --lesson slang_playground/sp07_gsplat2d_diff` |
| `slang_playground/sp08_autodiff` | Automatic Differentiation | `python -m slang_falcon.live --lesson slang_playground/sp08_autodiff` |
| `slang_playground/sp09_properties` | Properties | `python -m slang_falcon.live --lesson slang_playground/sp09_properties` |
| `slang_playground/sp10_generics` | Generics & Extensions | `python -m slang_falcon.live --lesson slang_playground/sp10_generics` |
| `slang_playground/sp11_operator_overload` | Operator Overload | `python -m slang_falcon.live --lesson slang_playground/sp11_operator_overload` |
| `slang_playground/sp12_lambda` | Lambda Expressions | `python -m slang_falcon.live --lesson slang_playground/sp12_lambda` |
| `slang_playground/sp13_painting` | Painting | `python -m slang_falcon.live --lesson slang_playground/sp13_painting` |
| `slang_playground/sp14_image_from_url` | Image From URL | `python -m slang_falcon.live --lesson slang_playground/sp14_image_from_url` |
| `slang_playground/sp15_variadic` | Variadic Generics | `python -m slang_falcon.live --lesson slang_playground/sp15_variadic` |

Smoke:

```powershell
python -m slang_falcon.live --lesson slang_playground/sp01_simple_color --once
python -m slang_falcon.live --lesson slang_playground/sp16_simple_image --once
python -m slang_falcon.live --lesson slang_playground/sp02_circle --once
python -m slang_falcon.live --lesson slang_playground/sp08_autodiff --once
```

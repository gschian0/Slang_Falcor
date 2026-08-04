# Neural trilogy — DiffSlang → neural shading → afternoon

Educational + runnable labs inspired by three posts (original lab text; cite, don’t copy):

| # | External post | Our phase | Start lesson |
|---|---------------|-----------|--------------|
| 1 | [Differentiable Slang](https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/) | `diffslang/` | `diffslang/d01_differentiable_attr` |
| 2 | [Get started with neural shading](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/) | `neural_shading/` | `neural_shading/ns01_trainable_pipeline` |
| 3 | [Neural Graphics in an Afternoon](https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/) | `neural_gfx_afternoon/` | `neural_gfx_afternoon/ng01_slangpy_calls` |

Quick bridges before the trilogy: `neural/n01`–`n04` (after Book of Shaders).

## Start the trilogy track

```powershell
cd d:\WindowsProgramming\Slang_Falcon
.\.venv\Scripts\Activate.ps1

python -m slang_falcon.lessons
python -m slang_falcon.live --lesson diffslang/d01_differentiable_attr
# ] advances through DiffSlang → neural_shading → afternoon
```

## Lesson ids

### DiffSlang
- `diffslang/d01_differentiable_attr`
- `diffslang/d02_fwd_bwd_intuition`
- `diffslang/d03_simt_vs_tensors`

### Neural shading
- `neural_shading/ns01_trainable_pipeline`
- `neural_shading/ns02_mlp_approx_shader`
- `neural_shading/ns03_freq_encoding`
- `neural_shading/ns04_coopvec_note`
- `neural_shading/ns05_slangpy_train_loop`

### Afternoon
- `neural_gfx_afternoon/ng01_slangpy_calls`
- `neural_gfx_afternoon/ng02_why_gradients`
- `neural_gfx_afternoon/ng03_gaussian_fit`
- `neural_gfx_afternoon/ng04_tiny_mlp_fit`

## Run this (CLI)

```powershell
# Hero BRDF MLP (post 2 / Lab 4)
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
python -m slang_falcon.infer --weights assets/weights/brdf_mlp.bin --out assets/output/brdf_compare.png

# Afternoon-style Gaussian fit (post 3)
python -m slang_falcon.fit_blobs --steps 400 --out assets/output/fit_blobs.png

# Smoke a live lesson once
python -m slang_falcon.live --lesson diffslang/d02_fwd_bwd_intuition --once --out assets/output/d02.png
python -m slang_falcon.live --lesson neural_gfx_afternoon/ng03_gaussian_fit --once --time 4 --out assets/output/ng03.png
```

## Themes covered (not verbatim)

- Autodiff as first-class (`[Differentiable]`, `fwd_diff` / `bwd_diff`)
- Why reverse mode dominates training; SIMT shaders ↔ tensor batches
- Inline MLPs approximating shaders; freq encoding; CoopVec = Phase 2 native
- SlangPy afternoon loop: call Slang → loss → grads → Adam → splat / MLP fit

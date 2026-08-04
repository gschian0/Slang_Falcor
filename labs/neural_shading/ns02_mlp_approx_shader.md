# NS02 — MLP approximates a shader

**Job:** teacher | tiny MLP | abs-diff — the get-started pattern for neural materials / lighting.

**Source post:** [How to Get Started with Neural Shading](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/)

**Also see:** `neural/n02_teacher_vs_neural` · Lab 4 · `neural_shading/ns05_slangpy_train_loop`

## Run

```powershell
python -m slang_falcon.live --lesson neural_shading/ns02_mlp_approx_shader
```

Three panels: analytic lighting slice | baked `2→8→3` net | `4×|diff|`.

## Train for real

```powershell
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
python -m slang_falcon.infer --weights assets/weights/brdf_mlp.bin --out assets/output/brdf_compare.png
```

Same idea as embedding a network in the shader: mark loss `[Differentiable]`, backprop, Adam, export weights for inference.

## Next

`neural_shading/ns03_freq_encoding`

Shader: `shaders/ns02_mlp_approx_shader.slang`.

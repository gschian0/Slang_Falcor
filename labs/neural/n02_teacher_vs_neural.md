# N02 — Teacher vs neural color/BRDF strip

**Job:** read a three-panel strip — analytic teacher | tiny MLP | abs-diff — the visual language of neural BRDF labs.

## Run

```powershell
python -m slang_falcon.live --lesson neural/n02_teacher_vs_neural
```

- **Left:** compact Disney-ish teacher (`ndotL` × roughness slice)
- **Middle:** baked `2→8→3` MLP (demo weights)
- **Right:** `4 × |teacher − mlp|` (brighter = worse match)

## Idea

Phase 1’s hero path trains a real MLP against Disney BRDF and exports `assets/weights/brdf_mlp.bin`. This live lesson keeps the **same strip layout** with a tiny in-shader net so you can explore without loading tensors.

## Train / infer the real net

```powershell
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
python -m slang_falcon.infer --weights assets/weights/brdf_mlp.bin --out assets/output/brdf_compare.png
```

See `labs/04_train_brdf.md` and `docs/weight_format.md`.

**Trilogy:** [`neural_shading/ns02_mlp_approx_shader`](../neural_shading/ns02_mlp_approx_shader.md) · train-loop map [`ns05`](../neural_shading/ns05_slangpy_train_loop.md) · [get-started post](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/)

## Try

1. Change albedo in `teacher_brdf` — watch the diff panel light up.
2. Nudge `wr` / `wg` / `wb` to reduce the right panel.
3. After training, compare this demo strip to `infer`’s PNG.

Shader: `shaders/n02_teacher_vs_neural.slang`.

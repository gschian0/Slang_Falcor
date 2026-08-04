# N01 — From function to network

**Job:** see a Book-of-Shaders shaping curve next to a tiny MLP that tries to match it.

## Run

```powershell
python -m slang_falcon.live --lesson neural/n01_function_to_network
```

Left panel: analytic `y = x³` (green). Right panel: baked `1→8→1` ReLU net (cyan). Both curves are overlaid so you can judge the fit.

## Idea

Classic fragment shaders *author* `f(x)`. Neural shading *approximates* `f` with a small network whose weights come from a teacher loss.

This lesson ships **inference with baked weights** so it runs in live without a train loop. The weights are hand-tuned demos — not a serious fit.

## Train for real (optional)

To train a BRDF MLP (bigger net, same idea):

```powershell
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
```

See Lab 4 (`labs/04_train_brdf.md`) and N02 for teacher vs neural strips.

**Trilogy:** same “function → network” idea deepens in [`neural_shading/ns02_mlp_approx_shader`](../neural_shading/ns02_mlp_approx_shader.md) · hub [`neural_trilogy`](../neural_trilogy/README.md).

## Try

1. Change `pow(st.x, 3.0f)` to `smoothstep(0.1f, 0.9f, st.x)` — watch the MLP lag behind.
2. Tweak `w0` / `w1` arrays and recompile (edit → debounce).
3. Widen the plot stroke in `plot`.

Shader: `shaders/n01_function_to_network.slang`.

# N04 — Live neural parameter

**Job:** connect Book-of-Shaders **uniforms** to neural graphics — `time` plus an editable gain drive a tiny net.

## Run

```powershell
python -m slang_falcon.live --lesson neural/n04_live_neural_param
```

Live injects `float time` (seconds). Edit `u_gain` in the side panel and wait for debounce — same workflow as BoS chapter 01.

## Idea

| BoS uniforms | Here |
|--------------|------|
| `u_time` / live `time` | animates a network input |
| hand-tuned float | `u_gain` scales the MLP output |
| `gl_FragColor = f(uv, uniforms)` | `color = net(uv, time, gain)` |

Neural shading doesn’t replace uniforms — it **consumes** them as features.

**Trilogy:** trainable-params vibe in [`neural_shading/ns01_trainable_pipeline`](../neural_shading/ns01_trainable_pipeline.md) · afternoon [`neural_gfx_afternoon/ng01`](../neural_gfx_afternoon/ng01_slangpy_calls.md)

## Try

1. Set `u_gain` to `0.4` vs `1.8` — exposure of the net.
2. Change the `sin(t * 1.7f + gain)` feature — different temporal mood.
3. Compare to `bos/01_uniforms` (pulse without a network).

## Train path

Uniforms in a real pipeline become MLP **inputs** (view, roughness, …). Train those weights with:

```powershell
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
```

Shader: `shaders/n04_live_neural_param.slang`.

# NS01 — Trainable pipeline

**Job:** see “authored shade” vs “same shade with drifting parameters” — neural shading’s core move.

**Source post:** [How to Get Started with Neural Shading](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/)

## Run

```powershell
python -m slang_falcon.live --lesson neural_shading/ns01_trainable_pipeline
```

Left: fixed gain/bias. Right: parameters wander with `time` (stand-in for an optimizer updating `GradOutTensor`s). Bottom bar: live gain readout.

## Idea

Neural shading = make part of the graphics pipeline **trainable**. Small networks (or even texture-like parameter fields) run inline in shaders; autodiff + an optimizer tune them offline or at bake time.

## Next

`neural_shading/ns02_mlp_approx_shader` — approximate a lighting slice with an MLP.

Shader: `shaders/ns01_trainable_pipeline.slang`.

# D01 — `[Differentiable]` as first-class

**Job:** treat autodiff as a language feature, not a separate framework.

**Source post:** [Differentiable Slang: A Shading Language for Renderers That Learn](https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/)

## Run

```powershell
python -m slang_falcon.live --lesson diffslang/d01_differentiable_attr
```

- **Left:** loss landscape `L = (field − target)²`
- **Right:** `|∂L/∂x|` — the nudge direction for the `x` parameter
- Yellow tick: a crawling parameter cursor

## Idea

Slang’s `[Differentiable]` attribute asks the compiler to generate forward and reverse derivative forms of your shader math. Graphics code and learning code share one source — Falcor-style differentiable path tracers and tiny MLP trainers both lean on this.

This lesson **visualizes** a loss and its gradient. Real emission of derivatives happens via `fwd_diff` / `bwd_diff` (next lesson) or SlangPy `.bwds` (Lab 2, Lab 4).

## Try

1. Change `field` — both panels should reshape.
2. Freeze `target` to a constant; compare to the breathing target.
3. Open `slang/train_brdf.slang` and find `bwd_diff(sample_loss)`.

## Next

`diffslang/d02_fwd_bwd_intuition` · hub: `labs/neural_trilogy/README.md`

Shader: `shaders/d01_differentiable_attr.slang`.

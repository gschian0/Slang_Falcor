# N03 — Autodiff intuition

**Job:** see a loss landscape and its gradient magnitude — what `[Differentiable]` is for.

## Run

```powershell
python -m slang_falcon.live --lesson neural/n03_autodiff_intuition
```

- **Left:** `L(x,y) = (field(x,y) − target)²` as a heatmap (`target` drifts with `time`)
- **Right:** `|∇L|` — how hard the loss pushes parameters in each direction
- Soft yellow ring: a moving reference point (not a trained optimizer)

## Idea

Training an MLP is “nudge weights so teacher − prediction shrinks.” That nudge is the **gradient** of a loss. Slang can generate those gradients from `[Differentiable]` functions; SlangPy exposes them via `.bwds` (Lab 2).

This lesson **visualizes** a tiny analytic loss and its hand-written gradient in pixels so the idea is geometric before you touch Tensor training.

**Trilogy (DiffSlang):** [`diffslang/d01_differentiable_attr`](../diffslang/d01_differentiable_attr.md) · [`d02_fwd_bwd_intuition`](../diffslang/d02_fwd_bwd_intuition.md) · [Differentiable Slang post](https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/)

## Next

```powershell
# Lab 2 notes
# labs/02_autodiff.md

# Real BRDF train (gradients through MLP)
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
```

## Try

1. Change `field` — watch both panels reshape.
2. Freeze `target` to a constant; compare to the breathing target.
3. Read Lab 2, then mark your own function `[Differentiable]`.

Shader: `shaders/n03_autodiff_intuition.slang`.

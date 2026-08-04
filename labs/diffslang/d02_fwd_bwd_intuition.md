# D02 — Forward vs backward intuition

**Job:** feel the difference between a directional derivative (fwd) and a parameter-space pull (bwd).

**Source post:** [Differentiable Slang](https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/) · Slang user guide: autodiff (`fwd_diff` / `bwd_diff`)

## Run

```powershell
python -m slang_falcon.live --lesson diffslang/d02_fwd_bwd_intuition
```

- **Left (fwd vibe):** seed a direction `v(t)` and show ⟨∇f, v⟩ — one Jacobian–vector product
- **Right (bwd vibe):** seed `dL/df = 1` and show `|∇f|` with flow along the gradient — what training usually wants

## Idea

| Mode | Operator | Typical use |
|------|----------|-------------|
| Forward | `fwd_diff(f)` | Few inputs → many outputs; sensitivity along a seed |
| Reverse | `bwd_diff(f)` | Many inputs → scalar loss; MLP / splat training |

Production pattern in this repo:

```slang
bwd_diff(sample_loss)(features, teacher, network, float3(1,1,1));
```

(`slang/train_brdf.slang`)

SlangPy wraps the same idea as `module.fn.bwds(...)` — see the Neural GFX afternoon track.

## Try

1. Watch the left panel’s seed rotate with `time`.
2. Mentally map: left = “push one direction through f”; right = “pull all parameters from a loss”.
3. Read Lab 2 (`labs/02_autodiff.md`).

## Next

`diffslang/d03_simt_vs_tensors`

Shader: `shaders/d02_fwd_bwd_intuition.slang`.

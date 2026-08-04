# Lab 2 — Autodiff 101

**Job:** mark a function `[Differentiable]`, run forward, then `bwd_diff` / `.bwds`.

## Idea

Neural shading is only useful if gradients flow through your shader math.
Slang generates the backward pass; SlangPy exposes it as `.bwds(...)`.

## Tiny function

In `slang/lab_kernels.slang`:

```slang
[Differentiable]
float polynomial(float a, float b, float c, float x)
{
    float y = a * x * x + b * x + c;
    return y * y;
}
```

## Python sketch (SlangPy Tensor path)

```python
import numpy as np
import slangpy as spy
from slang_falcon.device import get_device, load_module

device = get_device()
mod = load_module("lab_kernels")

# See slangpy autodiff docs for Tensor + .bwds patterns:
# https://slangpy.shader-slang.org/en/stable/src/autodiff/autodiff.html
print("Module loaded:", mod)
print("Try the official autodiff tutorial next, then jump to Lab 4.")
```

## Checkpoint

You understand: mark differentiable → forward → backward with seeded loss gradient.
Lab 4 applies the same idea to an MLP matching a Disney BRDF teacher.

**Live trilogy:** `diffslang/d01`–`d02` · hub `labs/neural_trilogy/README.md`

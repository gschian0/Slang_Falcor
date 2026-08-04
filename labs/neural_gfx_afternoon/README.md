# Neural Graphics in an Afternoon — lab port

Practical sequence from [Neural Graphics in an Afternoon](https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/).

| Id | Afternoon beat |
|----|----------------|
| `neural_gfx_afternoon/ng01_slangpy_calls` | Call Slang via SlangPy |
| `neural_gfx_afternoon/ng02_why_gradients` | Loss needs gradients |
| `neural_gfx_afternoon/ng03_gaussian_fit` | 2D Gaussian image fit |
| `neural_gfx_afternoon/ng04_tiny_mlp_fit` | Tiny MLP UV→RGB |

```powershell
python -m slang_falcon.live --lesson neural_gfx_afternoon/ng01_slangpy_calls
python -m slang_falcon.fit_blobs --steps 400 --out assets/output/fit_blobs.png
```

Hub: [`labs/neural_trilogy/README.md`](../neural_trilogy/README.md).

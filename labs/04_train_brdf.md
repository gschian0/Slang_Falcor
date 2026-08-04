# Lab 4 — Train a BRDF (hero)

**Job:** define a Disney teacher, train a tiny MLP, export weights, render a compare strip.

This is the Phase 1 exit criteria lab.

## Paradigm

```
teacher (analytic Disney)  →  train small MLP  →  infer in shader / export binary
```

You are **not** rewriting lighting by hand. The network absorbs the mapping from
features `(N·L, N·V, N·H, L·H, roughness)` → RGB.

## Run

```powershell
cd d:\WindowsProgramming\Slang_Falcon
pip install -e ".[dev]"

# Train (slangpy if GPU works, else numpy fallback)
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin

# Side-by-side: teacher | MLP | abs-diff
python -m slang_falcon.infer --weights assets/weights/brdf_mlp.bin --out assets/output/brdf_compare.png
```

Watch the loss printouts — it should trend down over steps.

## What to read in the repo

| Piece | Path |
|-------|------|
| Teacher | `slang/disney_brdf.slang` |
| MLP | `slang/mlp.slang` |
| Train / render kernels | `slang/train_brdf.slang` |
| CLI | `python/slang_falcon/train_brdf.py`, `infer.py` |
| Export format | `docs/weight_format.md` |

## Live notebook (optional)

```powershell
jupyter notebook labs/04_train_brdf.ipynb
```

## Checkpoint

You have:

1. `assets/weights/brdf_mlp.bin` (`SFMLP001`)
2. `assets/output/brdf_compare.png`
3. Intuition for Phase 2: Falcor loads the same file into a CoopVec inference pass

## Next

- Lab 5 (outline): approximate a texture instead of a BRDF  
- Lab 6: read `docs/weight_format.md` and skim `native/README.md`

# Shared Slang modules

| File | Role |
|------|------|
| `activations.slang` | ReLU / softplus helpers (teaching + native) |
| `disney_brdf.slang` | Analytic Disney teacher |
| `mlp.slang` | Differentiable `LinearLayer` + `BrdfMLP` |
| `lab_kernels.slang` | Lab 1–2 hello / autodiff sketches |
| `train_brdf.slang` | **SlangPy runtime entry** — self-contained MLP + teacher + train/infer |

Phase 1 CLI loads `train_brdf.slang` (single translation unit) so SlangPy module
visibility stays reliable. Split modules remain for docs, labs, and Phase 2 reuse.

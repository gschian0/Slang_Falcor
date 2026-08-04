# Neural shading — get started

Lessons mapped to [How to Get Started with Neural Shading](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/).

| Id | Title |
|----|-------|
| `neural_shading/ns01_trainable_pipeline` | Trainable pipeline |
| `neural_shading/ns02_mlp_approx_shader` | MLP ≈ shader |
| `neural_shading/ns03_freq_encoding` | Frequency encoding |
| `neural_shading/ns04_coopvec_note` | CoopVec / Phase 2 |
| `neural_shading/ns05_slangpy_train_loop` | SlangPy train loop |

```powershell
python -m slang_falcon.live --lesson neural_shading/ns01_trainable_pipeline
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
```

Hub: [`labs/neural_trilogy/README.md`](../neural_trilogy/README.md).

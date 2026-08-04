# NS05 — SlangPy train loop

**Job:** map the four stages of a neural-shading train step onto this repo’s CLIs.

**Source post:** [How to Get Started with Neural Shading](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/) (mipmap / network train sketches)

## Run

```powershell
python -m slang_falcon.live --lesson neural_shading/ns05_slangpy_train_loop
```

Animated schematic: **forward → loss → bwd → Adam → loop**.

## Loop (this playground)

| Stage | What happens | Where |
|-------|----------------|-------|
| Forward | Teacher + network predict | `slang/train_brdf.slang` `network.eval` |
| Loss | `(pred − teacher)²` marked `[Differentiable]` | `sample_loss` |
| Backward | `bwd_diff(sample_loss)(...)` fills weight grads | same file |
| Optimize | Adam on biases/weights | `BrdfNetwork.optimize` in Python |

```powershell
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
```

Afternoon track adds image-fit blobs:

```powershell
python -m slang_falcon.fit_blobs --steps 300 --out assets/output/fit_blobs.png
```

SlangPy pattern (conceptual — not a copy of NVIDIA samples):

1. `device = spy.create_device(...)` / `get_device()`
2. `module = load_module(...)`
3. Allocate tensors / network params (with grad storage when training)
4. Each step: call a train kernel that runs `bwd_diff` · then Adam · optionally preview

## Checkpoint

You can point at Lab 4 and the afternoon `fit_blobs` helper and know which stage each line is in.

## Next

`neural_gfx/ng01_slangpy_calls` — Neural Graphics in an Afternoon sequence.

Shader: `shaders/ns05_slangpy_train_loop.slang`.

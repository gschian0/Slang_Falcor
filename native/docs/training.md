# Phase 2 training + teacher/neural toggle

## Toggle

In the Falcor viewport (once wired):

| Key | Action |
|-----|--------|
| `T` | Cycle / toggle **teacher** vs **neural** shading |
| `F5` | Force hot-reload of `shaders/*.slang` |
| `R` | Run one `NeuralTrainPass::step()` when training enabled |

CLI:

```powershell
.\SlangFalconNative.exe --weights ..\assets\weights\brdf_mlp.bin --train --coopvec
```

## In-process training

`NeuralTrainPass` fine-tunes the same weight buffer used for inference:

1. Sample BRDF features (hemisphere L/V + roughness)
2. Evaluate Disney teacher (analytic)
3. Backprop through MLP (Slang autodiff; CoopVec `TrainingMLP` when available)
4. Adam update into the live buffer — inference sees updates next frame

Reference algorithm: `slang/train_brdf.slang` (Phase 1).

## CoopVec

When `VK_NV_cooperative_vector` is present, set `SF_USE_COOPVEC=1` and bind an
RTXNS-style `InferenceMLP` / `TrainingMLP`. Otherwise use the scalar path in
`NeuralBrdf.slang` for debug parity with Phase 1 images.

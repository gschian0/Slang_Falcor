# Neural lessons — BoS → Slang neural graphics

After the Book of Shaders → Slang track (`bos/00`–`05`) and optional **Slang Playground** ports (`slang_playground/sp01`…), these lessons fold the same live loop into **neural shading** ideas: approximate functions, teacher vs MLP, autodiff intuition, uniforms as network inputs.

Deeper trilogy (DiffSlang → get-started → afternoon): **[neural_trilogy/](../neural_trilogy/README.md)**

| Id | Title | Shader | Trilogy cross-link |
|----|-------|--------|--------------------|
| `neural/n01_function_to_network` | From function to network | `shaders/n01_function_to_network.slang` | → `neural_shading/ns02_mlp_approx_shader` |
| `neural/n02_teacher_vs_neural` | Teacher vs neural strip | `shaders/n02_teacher_vs_neural.slang` | → `train_brdf` / NS02 |
| `neural/n03_autodiff_intuition` | Autodiff intuition | `shaders/n03_autodiff_intuition.slang` | → `diffslang/d01`–`d02` |
| `neural/n04_live_neural_param` | Live neural parameter | `shaders/n04_live_neural_param.slang` | → `ns01_trainable_pipeline` |

## Run

```powershell
python -m slang_falcon.lessons
python -m slang_falcon.live --lesson neural/n01_function_to_network

# Or advance from BoS 05 with ] in the live window
python -m slang_falcon.live --lesson 0

# After N04, continue into DiffSlang:
python -m slang_falcon.live --lesson diffslang/d01_differentiable_attr
```

Training the full BRDF MLP (not required to view these demos):

```powershell
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
```

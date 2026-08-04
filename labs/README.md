# Labs — Neural shading curriculum

Tone: **define a teacher → train a small net → infer in the shader.**

We are not running a classic hand-authored lighting school.

| Lab | Title | Status |
|-----|--------|--------|
| 1 | Hello SlangPy (live edit) | Skeleton |
| 2 | Autodiff 101 | Skeleton |
| 3 | Your first MLP | Outline (optional) |
| 4 | Train a BRDF | **Hero** |
| 5 | Train a texture | Outline |
| 6 | Export for native | Points at `docs/weight_format.md` |

## Live curriculum (recommended path)

Ordered track in `labs/curriculum.json`:

1. **Book of Shaders → Slang** (`bos/00`–`05`)
2. **Slang Playground ports** (`slang_playground/sp01`–`sp15`) — after BoS  
   → **[slang_playground/](slang_playground/README.md)**
3. **Neural bridges** (`neural/n01`–`n04`)
4. **Neural trilogy** — DiffSlang → neural shading → afternoon  
   → **[neural_trilogy/](neural_trilogy/README.md)**

```powershell
python -m slang_falcon.lessons          # print ids + how to run
python -m slang_falcon.live --lesson 0  # start at bos/00_hello

# Jump to playground ports or trilogy:
python -m slang_falcon.live --lesson slang_playground/sp01_simple_color
python -m slang_falcon.live --lesson slang_playground/sp16_simple_image
python -m slang_falcon.live --lesson diffslang/d01_differentiable_attr

# In the live window (click away from the code panel):
#   ] or Right  next lesson
#   [ or Left   previous
#   L           list in console
```

Default `python -m slang_falcon.live` opens lesson 0 (BoS hello).

**Lab 1** (raw `lab_kernels` edit):

```powershell
python -m slang_falcon.live --shader slang/lab_kernels.slang
```

Then jump to Lab 4 once that works on your machine.

## Side tracks

| Path | Content |
|------|---------|
| [book_of_shaders/](book_of_shaders/README.md) | BoS chapters 00–05 |
| [slang_playground/](slang_playground/README.md) | Official Playground demos → `hello_pixel` |
| [neural/](neural/README.md) | Quick bridges N01–N04 |
| [diffslang/](diffslang/README.md) | DiffSlang themes |
| [neural_shading/](neural_shading/README.md) | Get-started neural shading |
| [neural_gfx_afternoon/](neural_gfx_afternoon/README.md) | Afternoon splat / MLP sequence |
| [neural_trilogy/](neural_trilogy/README.md) | URL → lesson map + run commands |
| [feedback/](feedback/README.md) | Vsynth-style feedback stub (simulated ping-pong) — [plan](../docs/plans/vsynth-feedback.md) |

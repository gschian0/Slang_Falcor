# VERNACULAR

**Agents / next session:** [`docs/CONTINUE.md`](docs/CONTINUE.md) · [`AGENTS.md`](AGENTS.md).  
**Runbook (how to operate):** [`docs/RUNBOOK.md`](docs/RUNBOOK.md).  
**Falcor 3D codebook:** [`docs/codebook/never_ending_slang.md`](docs/codebook/never_ending_slang.md) · `native/scripts/sync_vernacular_viewport.ps1 -Build`.

**VERNACULAR** — KodeLife-class live Slang IDE and neural shading school (Python package still `slang_falcon`). Round 1 status: [`docs/ROUND1.md`](docs/ROUND1.md). Product plan: [`docs/plans/vernacular.md`](docs/plans/vernacular.md).

A **school for technical artists** building **streamable / syndicable** programs on an

open stack (Khronos Slang, local playground, IP you can ship) — modern rendering and

neural shading **without** closed-toolkit lock-in. See [`docs/manifesto.md`](docs/manifesto.md).



Teach the **current** neural-shading paradigm: define a teacher, train a small MLP

inside shaders (Slang autodiff + SlangPy), then run inference in-shader — not

hand-authoring every lighting approximation.



```

Phase 1  SlangPy labs + train/infer CLI     ← ship first

Phase 2  Falcor / Vulkan CoopVec host       ← native parity + hot-reload

Phase 3  WebGPU demos                       ← browser contrast vs classic

```



## Quick start (Phase 1)



```powershell

cd d:\WindowsProgramming\Slang_Falcon

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"



# 1) Live curriculum (VERNACULAR) — BoS → Slang Playground → neural bridges → trilogy
python -m slang_falcon.lessons
python -m slang_falcon.live --lesson 0
# Or after pip install -e .: vernacular --lesson 0
# Playground ports (after BoS):
# python -m slang_falcon.live --lesson slang_playground/sp01_simple_color
# python -m slang_falcon.live --lesson slang_playground/sp16_simple_image
# Trilogy start:
# python -m slang_falcon.live --lesson diffslang/d01_differentiable_attr
# Editor unfocused: ] next · [ prev · L list
# Edit in the side panel, save → image updates. Esc exits FS / quits.

# Lab 1 raw kernel (optional):
# python -m slang_falcon.live --shader slang/lab_kernels.slang



# 2) Later: train a Disney-BRDF MLP and export weights

python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin



# 3) Render teacher | MLP | abs-diff strip

python -m slang_falcon.infer --weights assets/weights/brdf_mlp.bin --out assets/output/brdf_compare.png



# Afternoon-style Gaussian fit (optional)

python -m slang_falcon.fit_blobs --steps 400 --out assets/output/fit_blobs.png



# Smoke test

pytest -q

```



Open `labs/` for the teaching track. Live curriculum: **BoS 00–05** → **Slang Playground `sp01`–`sp16`** → **neural N01–N04** → **DiffSlang / neural_shading / afternoon** (`labs/curriculum.json`). Playground hub: [`labs/slang_playground/README.md`](labs/slang_playground/README.md). Trilogy hub: [`labs/neural_trilogy/README.md`](labs/neural_trilogy/README.md). Lab 4 remains the BRDF hero train path.

### Live options

```powershell
python -m slang_falcon.live --lesson 0
python -m slang_falcon.live --lesson bos/00_hello
python -m slang_falcon.live --lesson slang_playground/sp01_simple_color
python -m slang_falcon.live --lesson slang_playground/sp16_simple_image
python -m slang_falcon.live --lesson neural/n01_function_to_network
python -m slang_falcon.live --lesson diffslang/d01_differentiable_attr
python -m slang_falcon.live --lesson neural_gfx_afternoon/ng01_slangpy_calls
python -m slang_falcon.live --shader slang/lab_kernels.slang --entry hello_pixel --size 512
python -m slang_falcon.live --lesson 0 --once
python -m slang_falcon.live --lesson slang_playground/sp02_circle --once
python -m slang_falcon.live --lesson neural/n02_teacher_vs_neural --once --out assets/output/n02.png
```



Live preview is **VERNACULAR** — a **desktop pygame** mini IDE (not WebGPU). On save, SlangPy **compiles** the `.slang` module for the active GPU backend (Windows typically D3D12; Linux/macOS typically Vulkan or Metal; CUDA if available) — it does not transpile to JS/WGSL. Windowed mode: shader preview, code side panel (Slang highlighting), and a green terminal console for reload/errors. Editor: **Ctrl+Z** / **Ctrl+Y** undo/redo, select + **Ctrl+C/X/V**, resizable window (shader letterboxes). **F11** / green traffic light = **window fullscreen** (prefer this). **F10** / **Shift+F11** / cyan = **shader-only fullscreen** — **known issue: can black out the display**; prefer window FS for now (fix later; borderless windowed, never exclusive mode). **Esc** exits whichever FS mode is active (then quits when windowed). **W** toggles the Compiz-style wobble (off in fullscreen). ShaderToy ports (ocean, circle) use **2×2 in-shader supersample** for smoother edges.

On **Windows**, live preview uses a **borderless shaped window** with frosted Mac-style title chrome (traffic lights + iridescent title): the OS silhouette follows the jelly mesh via `SetWindowRgn` (color-key layered fallback if region setup fails). Move the window from the **title bar**, **Alt+drag**, or **middle-button** drag on the shader; interactive lessons (`interactive_mouse`, e.g. ocean) use primary-drag on the viewport for look-around. Non-Windows keeps a normal rectangular window for now.



## Hardware notes



| Phase | Needs |

|-------|--------|

| 1 | Any modern GPU that SlangPy / slang-rhi can drive (D3D12 or Vulkan). CPU fallback is not the goal. |

| 2 | Windows + VS2022, Vulkan SDK, NVIDIA driver with `VK_NV_cooperative_vector` (RTX 20xx+). Scalar fallback for debug. |

| 3 | Browser with WebGPU (Chrome/Edge). Float MLP inference only — no Tensor-Core CoopVec claim. |



## Repo layout



```

slang/          Shared .slang modules (MLP, activations, Disney teacher)

python/         slang_falcon package + CLI

labs/           Numbered teaching labs

docs/           Setup + weight export format + [manifesto](docs/manifesto.md) + [companion parable](docs/companion/robots_steal_coffee_from_babylon.md)

native/         VERNACULAR native / Falcor host (Phase 2)

web/            WebGPU demos (Phase 3)

assets/         Weights, reference / output images

tests/          Smoke pytest

```



## Future

- [Round 1 changelog](docs/ROUND1.md) — what ships today; next round = Falcor 3D
- [Companion parable](docs/companion/robots_steal_coffee_from_babylon.md) — robots / Babylon allegory: translate closed-stack “coffee” → open-stack Yerba Matte (French Press) / VERNACULAR ([manifesto](docs/manifesto.md))
- [VERNACULAR](docs/plans/vernacular.md) — KodeLife-class live Slang IDE + local AI helper (pinned on [roadmap](docs/roadmap.md)); package remains `slang_falcon`
- [Vsynth-style feedback patches](docs/plans/vsynth-feedback.md) — video feedback, patch graphs, differentiable diffusion as trainable feedback (pinned on [roadmap](docs/roadmap.md); stub [`labs/feedback/`](labs/feedback/))
- [Inline LLM / AI + SlangTorch realtime](docs/plans/llm-slang-torch-realtime.md) — host LLM assist + Torch/SlangPy bridge toward live neural inference (pinned on [roadmap](docs/roadmap.md))
- [Falcor viewport + Segment Anything](docs/plans/falcor-viewport-sam.md) — VERNACULAR native / Falcor 3D host, inline viewport AI, SAM2 on color+depth lift (pinned on [roadmap](docs/roadmap.md))
- [Audio shaders roadmap](docs/roadmap.md) — live-reload PCM via Slang compute (not Phase 3)

## Upstream references



- [Slang playground](https://shader-slang.org/slang-playground/)

- [slangpy docs](https://slangpy.readthedocs.io/)

- [Differentiable Slang](https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/) · [Get started with neural shading](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/) · [Neural Graphics in an Afternoon](https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/) — lab map in [`labs/neural_trilogy/README.md`](labs/neural_trilogy/README.md)

- [neural-shading-s25](https://github.com/shader-slang/neural-shading-s25) — course materials we curate against

- [RTXNS](https://github.com/NVIDIA-RTX/RTXNS) — CoopVec MLP patterns for Phase 2



## License



Apache-2.0 (aligns with Slang).



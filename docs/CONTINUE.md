# CONTINUE — handoff for the next Cursor agent

> Repo root may be renamed (`Slang_Falcon` → Falcor / `Slang_Falcor`, etc.). Prefer **relative paths**. Cursor often also reads [`AGENTS.md`](../AGENTS.md) at repo root.

**Date pinned:** 2026-08-03  
**Round 1:** complete — [`ROUND1.md`](ROUND1.md)

---

## Identity

| | |
|--|--|
| **Product** | **VERNACULAR** — KodeLife-class live Slang IDE + neural shading school for technical artists |
| **Package** | still `slang_falcon` (imports, CI, namespace) |
| **CLI** | `vernacular` (after `pip install -e .`) or `python -m slang_falcon.live` · also `python -m slang_falcon.vernacular` / `python -m slang_falcon.lessons` |
| **Manifesto** | [`manifesto.md`](manifesto.md) |
| **Companion allegory** | [`companion/robots_steal_coffee_from_babylon.md`](companion/robots_steal_coffee_from_babylon.md) — closed-stack “coffee” → open Yerba Matte / VERNACULAR |
| **Round 1 status** | [`ROUND1.md`](ROUND1.md) |

Teaching story: teacher → small MLP in shaders (Slang autodiff + SlangPy) → inference in-shader — not closed-toolkit lock-in.

---

## Done (Round 1)

### Live playground

- Hotswap editor (highlight, undo/redo, clipboard, select); temp recompile on edit; Save writes real `.slang`
- Lessons nav: `[` `]` / arrows, `L` list, `0`–`9` jump
- Compiz-style wobble chrome (`W`); two-square layout (shader | code) + console; resizable
- Mac-style frosted title chrome / shaped window on Windows
- **Dual fullscreen:** prefer **F11 / green** (window FS). **F10 / cyan** shader-only FS is **broken/pinned** — can black out the display; **do not polish live UI**; fix later with borderless windowed, never exclusive mode

### Curriculum

- Book of Shaders (BoS) labs
- Neural bridges **N01–N04**
- Neural trilogy (DiffSlang / neural_shading / afternoon) — hubs under `labs/neural_trilogy/`, `labs/slang_playground/`
- Slang Playground ports (`sp01`–`sp15`)
- Feedback stub: `labs/feedback/`
- Index: `labs/curriculum.json`

### Train / infer (Phase 1 CLIs)

- `train_brdf`, `infer`, `fit_blobs`; shared `slang/` MLP + Disney teacher

### Plans (pinned)

| Plan | Path |
|------|------|
| VERNACULAR product face | [`plans/vernacular.md`](plans/vernacular.md) |
| Falcor viewport + SAM | [`plans/falcor-viewport-sam.md`](plans/falcor-viewport-sam.md) |
| Vsynth-style feedback | [`plans/vsynth-feedback.md`](plans/vsynth-feedback.md) |
| LLM + SlangTorch realtime | [`plans/llm-slang-torch-realtime.md`](plans/llm-slang-torch-realtime.md) |
| Live playground polish | [`plans/live-playground-polish.md`](plans/live-playground-polish.md) |

Also: [`roadmap.md`](roadmap.md)

### Native / Falcor scaffold

- `native/` — weight load (`SFMLP001`), `NeuralBrdfPass` stubs, hot-reload, CMake hooks
- Falcor **8.0** may already be cloned under `native/external/Falcor` (gitignored) via `native/scripts/fetch_falcor.ps1`
- Phase 0 scaffold + stub app sketch exists; **mesh viewport NOT done** (no green 3D window yet)
- Details: [`../native/README.md`](../native/README.md)

### Git

- **No push / commit assumed** unless the user explicitly asks.

---

## Known issues / pins

| Issue | Guidance |
|-------|----------|
| **Shader-only fullscreen (F10 / cyan)** | Can **black out** the display. Use **F11 / green** only. Fix later; **do not** bikeshed live chrome unless asked. |
| Folder rename | May leave `Slang_Falcon`; rename manually when Cursor workspace lock allows. |
| Falcor mesh viewport | Phase 0 in progress — **this is the next coding milestone**. |

---

## NEXT (true priority)

1. **Falcor 3D Phase 0** — `VernacularViewport` sample + codebook:
   - Sources: `native/samples/VernacularViewport/`
   - Codebook: [`codebook/never_ending_slang.md`](codebook/never_ending_slang.md)
   - Build: `native/scripts/sync_vernacular_viewport.ps1 -Configure -Build` (see [`../native/README.md`](../native/README.md) § D)
   - Exit: navigable Falcor window, Slang chapters on meshes, F5 hot-reload — **no SAM yet**
2. Then Phase 1+ of [`plans/falcor-viewport-sam.md`](plans/falcor-viewport-sam.md) (viewport capture → SAM-on-viewport, etc.)
3. **Do not restart** live playground / Mac chrome / wobble polish unless the user asks

---

## Commands cheat sheet

Paths assume repo root. Activate venv first if needed: `.\.venv\Scripts\Activate.ps1` then `pip install -e ".[dev]"`.

```powershell
# Live curriculum (VERNACULAR)
python -m slang_falcon.lessons
python -m slang_falcon.live --lesson 0
# vernacular --lesson 0   # after pip install -e .
# Prefer F11 window FS; avoid F10 shader-only FS

# Examples
python -m slang_falcon.live --lesson bos/00_hello
python -m slang_falcon.live --lesson slang_playground/sp01_simple_color
python -m slang_falcon.live --lesson slang_playground/sp16_simple_image
python -m slang_falcon.live --lesson neural/n01_function_to_network
python -m slang_falcon.live --lesson diffslang/d01_differentiable_attr

# Train BRDF MLP
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
python -m slang_falcon.infer --weights assets/weights/brdf_mlp.bin --out assets/output/brdf_compare.png

# Smoke
pytest -q

# Native scaffold (no Falcor)
cd native
cmake -B build -G "Visual Studio 17 2022" -A x64 -DSF_BUILD_STANDALONE=ON
cmake --build build --config Release
.\build\Release\SlangFalconNative.exe --weights ..\assets\weights\brdf_mlp.bin

# Fetch Falcor 8.0 (large) then configure — see native/README.md
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_falcor.ps1
```

Round 1 changelog: [`ROUND1.md`](ROUND1.md).

---

## How to continue (first actions for the next agent)

1. Read [`RUNBOOK.md`](RUNBOOK.md) first — exact run / rebuild / fix table.
2. Then this file + [`ROUND1.md`](ROUND1.md) + [`plans/falcor-viewport-sam.md`](plans/falcor-viewport-sam.md).
3. 3D show: `native/scripts/sync_vernacular_viewport.ps1 -Build` then `VernacularViewport.exe` (paths in RUNBOOK).
4. Do **not** touch F10 / live UI polish unless asked.
5. Do **not** commit or push unless the user explicitly asks.

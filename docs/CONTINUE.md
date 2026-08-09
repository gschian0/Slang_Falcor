# CONTINUE — handoff for the next Cursor agent

> Repo root may be renamed (`Slang_Falcon` → Falcor / `Slang_Falcor`, etc.). Prefer **relative paths**. Cursor often also reads [`AGENTS.md`](../AGENTS.md) at repo root.

**Date pinned:** 2026-08-04  
**Round 1:** complete — [`ROUND1.md`](ROUND1.md)  
**3D show:** Temple of Secret Knowledge (Iteration 3) — Vibration Modes pinned (Iteration 2, `F3`) · Orbit/Fly (Iteration 4) · spatial audio (Iteration 5)

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
| **3D codebook** | [`codebook/never_ending_slang.md`](codebook/never_ending_slang.md) — Temple (active) · Vibration Modes (pinned) |
| **Omniverse** | [`plans/vernacular-omniverse-bridge.md`](plans/vernacular-omniverse-bridge.md) — compose later; not Kit today |

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
| 3D environment shading school *(Temple = Iteration 3 active)* | [`plans/vernacular-3d-lesson-world.md`](plans/vernacular-3d-lesson-world.md) |
| Omniverse compose note | [`plans/vernacular-omniverse-bridge.md`](plans/vernacular-omniverse-bridge.md) |
| Falcor viewport + SAM | [`plans/falcor-viewport-sam.md`](plans/falcor-viewport-sam.md) |
| Vsynth-style feedback | [`plans/vsynth-feedback.md`](plans/vsynth-feedback.md) |
| LLM + SlangTorch realtime | [`plans/llm-slang-torch-realtime.md`](plans/llm-slang-torch-realtime.md) |
| Live playground polish | [`plans/live-playground-polish.md`](plans/live-playground-polish.md) |
| Viewport iterations | [`plans/vernacular-viewport-iterations.md`](plans/vernacular-viewport-iterations.md) |

Also: [`roadmap.md`](roadmap.md)

### Native / Falcor scaffold

- `native/` — weight load (`SFMLP001`), `NeuralBrdfPass` stubs, hot-reload, CMake hooks
- Falcor **8.0** may already be cloned under `native/external/Falcor` (gitignored) via `native/scripts/fetch_falcor.ps1`
- **`VernacularViewport` primary show:** Temple of Secret Knowledge (ocean / land / sky + three canvases)
- **Pinned:** Vibration Modes of Cube — `F3` / `ShowMode::VibrationModes` (Iteration 2)
- Details: [`../native/README.md`](../native/README.md)

### Git

- **No push / commit assumed** unless the user explicitly asks.

---

## Known issues / pins

| Issue | Guidance |
|-------|----------|
| **Shader-only fullscreen (F10 / cyan)** | Can **black out** the display. Use **F11 / green** only. Fix later; **do not** bikeshed live chrome unless asked. |
| Folder rename | May leave `Slang_Falcon`; rename manually when Cursor workspace lock allows. |
| Vibration Modes | Pinned Iteration 2 — keep behind `F3`; do not delete without documenting restore. |
| Omniverse | Falcor SampleApp only today — see bridge note. |

---

## NEXT (true priority)

1. **Temple of Secret Knowledge** (primary 3D show) — harden ocean/land/sky + canvas bank:
   - Sources: `native/samples/VernacularViewport/`
   - Codebook: [`codebook/never_ending_slang.md`](codebook/never_ending_slang.md)
   - Build: `native/scripts/sync_vernacular_viewport.ps1 -Build` (see [`RUNBOOK.md`](RUNBOOK.md))
   - Audio: Iteration 5 `VernacularSoundscape` (spatial bowl / distance / Doppler) — [`plans/vernacular-viewport-spatial-audio.md`](plans/vernacular-viewport-spatial-audio.md)
   - Optional: richer school ports, USD export sketch, chirp sources / HRTF
2. Vibration Modes remain one `F3` away — extend only if asked
3. Later: SAM · inline AI image/post · Omniverse USD path
4. **Do not restart** live playground / Mac chrome / wobble polish unless the user asks
5. **No** ORCA / PathTracer / Emerald Square as the primary loop

---

## Commands cheat sheet

Paths assume repo root. Activate venv first if needed: `.\.venv\Scripts\Activate.ps1` then `pip install -e ".[dev]"`.

```powershell
# Live curriculum (VERNACULAR)
python -m slang_falcon.lessons
python -m slang_falcon.live --lesson 0
# Prefer F11 window FS; avoid F10 shader-only FS

# Native 3D show
cd native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build
# Run: native\external\Falcor\build\windows-vs2022\bin\Release\VernacularViewport.exe

# Smoke
pytest -q
```

Round 1 changelog: [`ROUND1.md`](ROUND1.md).

---

## How to continue (first actions for the next agent)

1. Read [`RUNBOOK.md`](RUNBOOK.md) first — exact run / rebuild / controls.
2. Then [`codebook/never_ending_slang.md`](codebook/never_ending_slang.md) + this file.
3. 3D show: `native/scripts/sync_vernacular_viewport.ps1 -Build` then `VernacularViewport.exe`.
4. Do **not** touch F10 / live UI polish unless asked.
5. Do **not** commit or push unless the user explicitly asks.

# Round 1 — VERNACULAR

**Date pinned:** 2026-08-03  
**Product name:** **VERNACULAR** (KodeLife-class live Slang IDE + neural shading school)  
**Implementation package:** `slang_falcon` (unchanged imports / CI)  
**Checkout folder:** `Slang_Falcon` — **do not force-rename** while Cursor has the workspace locked; rename the Windows folder manually later if desired.

This is **Round 1**: the live 2D Slang playground, curriculum, manifesto/companion, and planning docs. **Falcor 3D is not shipping yet** — that is the next round.

Plan face: [plans/vernacular.md](plans/vernacular.md) · Roadmap: [roadmap.md](roadmap.md)

---

## What ships in Round 1

- **VERNACULAR live IDE** — `python -m slang_falcon.live` / `python -m slang_falcon.vernacular` / console script `vernacular` after `pip install -e .`
  - In-window Slang editor (highlight, undo/redo, clipboard, select)
  - Temp hotswap recompile on edit; Save writes the real `.slang`
  - Two-square layout (shader | code) + console; resizable; Windows shaped Compiz-style wobble chrome
  - Curriculum keys: `[` `]` / arrows, `L` list, `0`–`9` jump
- **Curriculum** — BoS → Slang Playground ports → neural bridges → DiffSlang / neural_shading / afternoon trilogy (`labs/curriculum.json`); feedback stub under `labs/feedback/`
- **Train / infer CLIs** — `train_brdf`, `infer`, `fit_blobs`; shared `slang/` MLP + Disney teacher
- **Docs** — [manifesto](manifesto.md), [companion parable](companion/robots_steal_coffee_from_babylon.md), pinned plans (VERNACULAR, LLM/SlangTorch, Falcor+SAM, Vsynth feedback, live polish)
- **VERNACULAR native / Falcor host scaffold** — `native/` weight load + NeuralBrdf stubs; Falcor fetch script; clone may exist at `native/external/Falcor` (gitignored); **no green 3D mesh viewport yet**

---

## Known issues (pinned — fix later)

| Issue | Guidance |
|-------|----------|
| **Shader-only fullscreen (F10 / cyan)** | Can **black out** the display. Prefer **window fullscreen (F11 / green)** for now. Fix later with **borderless windowed**, never exclusive fullscreen mode. |
| Windows folder still named `Slang_Falcon` | Manual rename later; Cursor workspace lock. |
| Falcor mesh viewport | Phase 0 in progress — next round. |

Also noted in [plans/live-playground-polish.md](plans/live-playground-polish.md) and [roadmap.md](roadmap.md).

---

## Next round

**Falcor 3D viewport** — wire VERNACULAR native host to a SampleApp / Mogwai-style minimal scene (mesh + camera + Slang pass). See [plans/falcor-viewport-sam.md](plans/falcor-viewport-sam.md) Phase 0 and [../native/README.md](../native/README.md).

# Plan: VERNACULAR 3D lesson world (Falcor)

**Status:** Phase A started (Shader Man + findable lesson markers)  
**Product:** Main school lives in **Falcor 3D** — walk, find shaders, read what they do, edit, later hear/speak and NPU-assist.  
**2D live** (`slang_falcon.live`) stays the deep editor / curriculum bank; Falcor is the **world**.

Related: [falcor-viewport-sam.md](falcor-viewport-sam.md) · [llm-slang-torch-realtime.md](llm-slang-torch-realtime.md) · [manifesto.md](../manifesto.md)

---

## Vision (what you asked for)

| Piece | Intent |
|-------|--------|
| **3D lessons** | Curriculum stations in the world — text explains *why this is a 3D lesson* and what the shader does |
| **Falcor = main program** | Atmosphere + ocean + folds stay; the world is where you learn |
| **Game access** | Walk (Shader Man) to codes; proximity unlocks explain + enter/edit |
| **Inline edit** | Edit `.slang` in-world (panel) or hand off to 2D live for full chrome |
| **TTS** | Speak the lesson blurb / Try tips (later) |
| **LLM on NPU** | Generate / expand lesson text inline on device (later) |
| **Shader Man** | 3rd-person weird character = **UV boxes** with cool analytic shaders |

---

## Sequence (do not skip)

### Phase A — Walkable findables *(now)*

- Third-person **Shader Man** (stacked UV cubes, live Slang look)
- **Lesson markers** in the environment (walk up → HUD / desk text)
- **E** enter → open matching 2D lesson (or inline read-only code soon)
- Keep atmosphere desk, ocean, folds

### Phase B — Inline codes

- In-Falcor code panel for the active station (hot-reload into a local pass or shared kernel)
- Save back to `labs/...` when safe
- Station list / map UI

### Phase C — Voice

- TTS reads banner / blurb (Windows SAPI or local Piper)
- Optional: mute, rate, “read Try tips”

### Phase D — NPU / LLM assist

- Local small LLM (NPU / DirectML / ONNX) expands “what does this do?” next to the station
- Never blocks offline labs — assist is optional (manifesto: agency)

### Phase E — SAM + viewport AI

- Align with [falcor-viewport-sam.md](falcor-viewport-sam.md) once the world loop is fun

---

## Non-goals (for A–B)

- Not a AAA animation system — UV-box man is the aesthetic
- Not exclusive fullscreen / F10 paths
- Not cloud-only LLM as the default teacher

---

## Exit checks

| Phase | Done when |
|-------|-----------|
| A | Walk Shader Man, find ≥3 stations, text explains 3D lesson, **E** opens live lesson |
| B | Edit a station shader without leaving Falcor (or one-key round-trip) |
| C | Hear one blurb spoken |
| D | One NPU/local generate button produces text for a station |

---

*Pinned: world first → edit → speak → NPU text → SAM.*

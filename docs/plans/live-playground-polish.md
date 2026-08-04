# Plan: Live playground polish (navigation + resize)

**Pinned on:** [docs/roadmap.md](../roadmap.md)  
**Status:** **live IDE chrome pinned / good enough** — dual fullscreen, shaped wobble host, two-square layout, curriculum keys, and editor basics ship. Remaining polish is optional; **primary focus moves to 3D Falcor** ([falcor-viewport-sam.md](falcor-viewport-sam.md) Phase 0+).  
**Goal (historical):** Make the pygame live window easier to browse as a lesson track, and keep the larger resizable layout solid. Build on what already ships; do not reinvent the preview loop.

---

## Known issue (pinned — do not polish live UI for this now)

| Issue | Guidance |
|-------|----------|
| **Shader-only fullscreen (F10 / Shift+F11 / cyan traffic light)** | Can **black out** the display. Prefer **window fullscreen (F11 / green)** for now. **Fix later:** borderless windowed path; **never** exclusive fullscreen mode. |

See also [ROUND1.md](../ROUND1.md).

---

## Current state

Inspected: `python/slang_falcon/live.py`, `curriculum.py`, `lessons.py`, `code_editor.py`, README “Live options”.

### Already works today (pinned chrome)

| Area | Behavior |
|------|----------|
| **Start a lesson** | `--lesson` accepts index (`0`), full id (`bos/00_hello`), or suffix; default with no `--shader` is curriculum lesson 0 |
| **CLI list** | `python -m slang_falcon.lessons` (and `--json`) prints phases / ids / how to run |
| **In-window nav (keys)** | Editor **unfocused**: `[` / Left = prev, `]` / Right = next, `L` = dump list to console, `0`–`9` = jump by index |
| **Lesson chrome** | Caption / title bar show `VERNACULAR — index:title`; switch loads shader + entry, resets `time`, hotswaps |
| **Larger default** | `_DEFAULT_LIVE_SIZE = 640`; `--size` / `--width` / `--height` override |
| **Resizable** | `pygame.RESIZABLE`; `VIDEORESIZE` → `apply_client_size` (min client size, wobble pad aware) |
| **Reflow** | Layout letterboxes shader; two-square shader\|code when possible; console fixed height |
| **Editor** | Ctrl+Z undo, Ctrl+Y / Ctrl+Shift+Z redo, select (drag / Shift+arrows), Ctrl+C/X/V |
| **Chrome buttons** | Save / Reload (disk); traffic lights: red close · green **window FS** · cyan **shader FS** (prefer green) |
| **Dual fullscreen** | **F11** / green = window FS (prefer); **F10** / **Shift+F11** / cyan = shader-only (**known blackout risk**); **Esc** exits FS (then quits when windowed) |
| **Wobble / mouse-look** | Compiz wobble + shaped Windows silhouette when windowed; interactive lessons keep shader drag look-around |

### Optional gaps (not blocking Falcor)

| Gap | Today |
|-----|--------|
| **Lesson browser UI** | List is console-only (`L` / CLI); no in-window picker yet |
| **On-screen next/prev** | Keyboard only when editor unfocused |
| **Wider defaults / resize polish** | Edge-case reflow (shaped pad, very tall/wide) — nice-to-have |

---

## Non-goals

- **No Falcor** in this plan (viewport / SAM / native host stay on [falcor-viewport-sam.md](falcor-viewport-sam.md)).
- No WebGPU / browser live port.
- No LLM assist UI (see [llm-slang-torch-realtime.md](llm-slang-torch-realtime.md)).
- Do not block on redesigning the Compiz wobble or borderless Windows chrome — treat as **done enough**.
- Do **not** keep polishing live UI for shader-only FS until the pinned fix (borderless windowed).

---

## Future work (optional only)

### 1. Lesson browser UI

Overlay / side list toggled by `L` (or a “Lessons” button); keep `[` `]` / arrows / `0–9` / CLI.

### 2. On-screen next / prev

Prev / Next on the button bar beside Save / Reload for when the code panel is focused.

### 3. Resize / prefs polish

Harden shaped HWND resize; optional remember-last-size prefs.

### 4. Shader-only FS fix (pinned)

Replace exclusive / display-blackout path with borderless windowed covering the work area; keep window FS as the safe default.

---

## Success checks (if polishing later)

- From a cold start, a new user can move BoS → neural without memorizing keys or leaving the window.
- Resize still letterboxes the shader and keeps code/console usable down to the documented minimum.
- Falcor / SAM / LLM plans remain the active implementation track.
- Shader-only FS no longer blacks out the display.

# fb01 — Ping-pong feedback (simulated)

**Job:** feel classic **video feedback** — zoom / rotate previous “frame,” blend with fresh ink, control persistence.

**Plan:** [docs/plans/vsynth-feedback.md](../../docs/plans/vsynth-feedback.md) (F0).

## Honest limit

`slang_falcon.live` today is **single-pass** `hello_pixel` → RGB. There is **no** ping-pong render target or previous-frame texture bind yet.

This lesson **simulates** feedback with a time-based trail of stamped shapes (same compromise as the playground painting port). True F0 needs a small live extension: two buffers, sample previous each frame, `feedback` uniform.

## Run

```powershell
python -m slang_falcon.live --lesson feedback/fb01_pingpong
python -m slang_falcon.live --lesson feedback/fb01_pingpong --once
```

## Try

1. Change `feedback` (decay) — longer trails vs snappy fade.
2. Tweak `zoom` / `spin` — spiral vs breathing zoom.
3. When live grows ping-pong RTs, replace the stamp loop with a sample of the previous buffer + blend.

Shader: `shaders/fb01_pingpong.slang`

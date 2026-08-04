# Feedback — Vsynth-style stubs

Side track for **video feedback** / patch ideas. Full plan: [`docs/plans/vsynth-feedback.md`](../../docs/plans/vsynth-feedback.md).

| Lesson | Title | Notes |
|--------|-------|--------|
| `feedback/fb01_pingpong` | Ping-pong feedback (simulated) | Time-based trails — live has no prev-frame RT yet |

```powershell
python -m slang_falcon.live --lesson feedback/fb01_pingpong
```

True ping-pong (two buffers + previous-frame sample) is **F0 host work** in the plan — not a live IDE rewrite.

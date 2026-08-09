# VernacularViewport — Iteration 5 spatial audio

**Status:** Implemented 2026-08-09 in Falcor `VernacularViewport`.  
**Sample:** `native/samples/VernacularViewport/`  
**Engine:** `VernacularSoundscape.{h,cpp}`  
**Iteration log:** [`vernacular-viewport-iterations.md`](vernacular-viewport-iterations.md)

Camera = listener. Graphics never waits on audio. Mute remains **M**.

---

## Why not miniaudio / FMOD

| Option | Verdict |
|--------|---------|
| **FMOD** | Out of scope (license + ship weight). |
| **miniaudio** (MIT / public domain, WASAPI on Windows) | Recommended in research, but Falcor samples build `/W4 /WX`. Vendoring `miniaudio.h` (~90k lines) into that warning regime + shallow sync of the sample tree is slower and riskier than extending the Iteration 3 WASAPI path. |
| **WASAPI shared mix** (this pass) | Already proven fail-soft in-sample. Doppler, 1/r, and equal-power pan are host math — they do not need a third-party device layer. |

Backend can swap later (miniaudio / Kit audio) without changing the physics API on `VernacularSoundscape`.

---

## Listener

Each frame, from Orbit / Fly camera:

| Field | Source |
|-------|--------|
| position | `Camera::getPosition()` (eye) |
| forward | yaw/pitch look vector |
| up | world +Y |
| velocity | finite difference `(eye - lastEye) / dt`, clamped to sane dt; reset on show-mode rebuild so the camera jump does not spike Doppler |

---

## Sources (omnidirectional / spherical)

| Slot | Kind | Attach | Notes |
|------|------|--------|-------|
| 0 | **Bowl** | Temple lesson plane `(0, 2.05, 0)` · Vibration grid center `(0, 1.2, -0.5)` | 3 sines; ~0.5–4 Hz beat. Stronger when looking at / near the plane (`lookBoost`). |
| 1 | **Atmosphere** | Distant bed `(0, 12, -28)` | One-pole filtered noise; Temple only; quiet. |
| 2–4 | **ChirpHook** | — | Reserved bird/chirp points. Silent this pass. |

Chapter coupling: Ch0 UV is the classic ~120 / 122 Hz delta preset. Other chapters reuse the same bowl with a slight `f0` shift (`+3.25 Hz` per chapter) and beat still in 0.5–4 Hz. No full preset table.

---

## Physics

World units are treated as **meters**.

### Distance (spherical spreading)

```
gain = clamp(refDist / max(dist, minDist), 0, 1)
then fade linearly 1 → 0 from fadeStart … maxDist
```

| Constant | Value | Role |
|----------|-------|------|
| `kMinDistance` | 1.5 m | Avoid 1/r blow-up at the emitter |
| `kRefDistance` | 4.0 m | Unity-gain reference |
| `kFadeStart` | 20 m | Start extra fade |
| `kMaxDistance` | 36 m | Silence beyond |

Default Temple orbit (~11 m) sits near `4/11 ≈ 0.36` spreading — present but not loud. Wheel-zoom in/out should read clearly.

### Stereo pan

Listener-space azimuth via `dot(normalize(src - ear), right)` where `right = normalize(forward × up)`. Equal-power:

```
angle = (pan + 1) * π/4     // pan -1…+1
L = cos(angle),  R = sin(angle)
```

No HRTF this pass.

### Doppler

```
f' = f * (c + v_listener_radial) / (c + v_source_radial)
c  = 343 m/s
```

Signs (classic acoustics):

- `v_listener_radial` **> 0** when the listener moves **toward** the source  
- `v_source_radial` **> 0** when the source **recedes** from the listener  

Sources are static (`velocity = 0`) this pass; orbit / fly listener motion still Doppler-shifts the bowl. Ratio clamped to **0.88 … 1.15** so a fast RMB orbit does not go cartoon. Atmosphere noise is not pitch-shifted. F1 checkbox disables Doppler.

---

## Integration

| Hook | Behavior |
|------|----------|
| `onLoad` | `mSoundscape.start()` — fail-soft |
| `onShutdown` / destructor | `mSoundscape.stop()` |
| each `onFrameRender` | update listener + sources from camera / chapter / show |
| **M** | mute (kept) |
| **F1** | mute, master gain, Doppler checkbox, status + debug line (`bowl Xm gain dop pan`) |

Unsupported mix formats stay silent (float32 + pcm16 written). Non-Windows: status stub, no thread.

---

## Non-goals / stubs

- Omniverse / Kit audio  
- GPU / Slang PCM  
- FMOD / HRTF  
- Moving sources, bird chirps (hooks only)  
- Per-chapter preset bank  

---

## Rebuild / run

```powershell
cd native
powershell -ExecutionPolicy Bypass -File .\scripts\sync_vernacular_viewport.ps1 -Build
# exe: native\external\Falcor\build\windows-vs2022\bin\Release\VernacularViewport.exe
```

Hear: Ch0 bowl on the plane · orbit closer = louder · fly past = Doppler · **M** mute · graphics survives a dead endpoint.

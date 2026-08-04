# Phase 3 — WebGPU demos

Browser demos that show **where neural shading shines** vs classic methods —
compression / approximation quality / authoring speed — without claiming
Tensor-Core CoopVec in-browser.

## Run locally

```powershell
cd d:\WindowsProgramming\Slang_Falcon\web
# Any static server:
python -m http.server 8080
# Open http://localhost:8080/
```

Or open `web/index.html` directly in Chrome/Edge (file weights may need the server).

## Demos

| Demo | Story |
|------|--------|
| `demos/brdf_compare.html` | Analytic Disney teacher vs MLP (loads `SFMLP001`) |
| `demos/texture_footprint.html` | Classic texture vs neural-approx footprint intuition |
| `demos/when_to_use.html` | WebGPU = teach/share; native CoopVec = production speed |

## Weights

Copy or serve Phase 1 export:

```
assets/weights/brdf_mlp.bin
```

The page fetches `../assets/weights/brdf_mlp.bin` relative to `web/` when using
`python -m http.server` from `web/` you may need:

```powershell
cd d:\WindowsProgramming\Slang_Falcon
python -m http.server 8080
# http://localhost:8080/web/
```

## Exit criteria

Static site under `web/` runnable locally; BRDF demo uses exported Phase 1 weights.

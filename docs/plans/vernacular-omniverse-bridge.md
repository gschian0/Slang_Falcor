# VERNACULAR ↔ Omniverse bridge (short)

**Question:** Will VernacularViewport run inside Omniverse?

**Honest answer: not today.** The 3D host is a **Falcor `SampleApp`** (`VernacularViewport.exe`), not Omniverse Kit / Carbonite. Do not claim the exe embeds in Kit.

## What composes with Omniverse / USD / RTX research

| Portable now / soon | Stays Falcor-local (for now) |
|---------------------|------------------------------|
| Slang lesson kernels (`lessons/*.slang`, shading ladder looks) | SampleApp orbit/fly loop, ImGui menus |
| Analytic ocean / sky / land looks (math, not engine) | WASAPI delta-tone stub |
| Future: author `.usda` stage (ocean/land/sky + three canvases) | Falcor scene builder meshes |
| Later: MaterialX / UsdPreviewSurface mapping of looks | Falcor `RasterPass` analytic path |

## Suggested Omniverse path (later)

1. Export / author a USD stage with ocean surface, distant land, sky dome, plane + sphere + cube canvases.
2. Drive canvas looks via materials / primvars (or custom MDL/MaterialX that mirrors Slang chapter ids).
3. Keep VERNACULAR 2D live (`slang_falcon.live`) as the shader school desk; Kit as the research viewport that consumes the same kernels / USD layout.
4. Spatial audio in Omniverse uses Kit audio extensions — not this WASAPI stub.

## Product stance

VERNACULAR **composes with** Omniverse / USD / RTX research surfaces (shaders, papers, stages) rather than rewriting a second “hamster-wheel Unix” engine. Falcor remains the fast analytic classroom; Omniverse is an optional research destination for the same looks and layout.

*Iteration 3 — 2026-08-04. See [`vernacular-viewport-iterations.md`](vernacular-viewport-iterations.md).*

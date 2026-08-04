# Setup (Phase 1)

## Prerequisites

- Windows 10/11 (also works on Linux/macOS for Phase 1)
- Python 3.10+
- A GPU with current drivers (D3D12 or Vulkan via slang-rhi)

CoopVec Tensor Cores are **not** required until Phase 2.

## Install

```powershell
cd d:\WindowsProgramming\Slang_Falcon
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Verify

```powershell
# Live preview (primary Lab 1 path — needs a display)
python -m slang_falcon.live

# Headless smoke of the same kernel
python -m slang_falcon.live --once --out assets/output/lab1_hello.png

python -m slang_falcon.train_brdf --steps 50 --backend numpy --out assets/weights/smoke.bin
python -m slang_falcon.infer --weights assets/weights/smoke.bin --backend numpy
pytest -q
```

`--backend numpy` is a CPU reference path used when slangpy/GPU is unavailable.
Prefer `--backend slangpy` (or `auto`) when a GPU device creates successfully.

## Labs

See `labs/README.md`. Lab 1 starts with live edit; Lab 4 is the BRDF hero path.

## References

- [slangpy docs](https://slangpy.readthedocs.io/)
- [Slang playground](https://shader-slang.org/slang-playground/)
- [neural-shading-s25](https://github.com/shader-slang/neural-shading-s25)

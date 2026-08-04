# Lab 1 — Hello SlangPy

**Job:** open a live window, edit a kernel, see pixels update.

## Idea

SlangPy loads a `.slang` module and calls functions as if they were Python.
The first checkpoint is: **change a return color, save, watch the window update** —
not write-a-PNG-and-open.

## Steps

1. Install the package (`pip install -e .`) — see `docs/setup.md`.
2. Start live preview:

```powershell
python -m slang_falcon.live
```

3. Open `slang/lab_kernels.slang` and edit `hello_pixel` — for example change the return to a solid color or tweak the UV math:

```slang
return float3(uv.y, uv.x, 0.75f);
// or: return float3(1.0f, 0.2f, 0.1f);
```

4. **Save the file.** The window recompiles and refreshes. Errors print in the console; the last good frame stays on screen.
5. Close the window (or press Esc) when done.

### Options

```powershell
python -m slang_falcon.live --entry hello_pixel --size 512
python -m slang_falcon.live --once --out assets/output/lab1_hello.png   # no GUI
```

## Shader

See `slang/lab_kernels.slang` → `hello_pixel`.

## Optional: one-shot PNG (no live window)

If you need a file for a notebook or CI:

```python
from pathlib import Path
import numpy as np
from PIL import Image

try:
    import slangpy as spy
    from slang_falcon.device import get_device, load_module

    device = get_device()
    mod = load_module("lab_kernels")
    w, h = 256, 256
    out = spy.Tensor.empty(device, shape=(h, w), dtype=spy.float3)
    mod.hello_pixel(pixel=spy.call_id(), resolution=spy.int2(w, h), _result=out)
    img = np.clip(out.to_numpy() * 255.0, 0, 255).astype(np.uint8)
except Exception as exc:
    print("slangpy path unavailable:", exc)
    ys, xs = np.mgrid[0:256, 0:256]
    img = np.stack([xs / 255, ys / 255, np.full_like(xs, 0.25, dtype=float)], axis=-1)
    img = (img * 255).astype(np.uint8)

Path("assets/output").mkdir(parents=True, exist_ok=True)
Image.fromarray(img).save("assets/output/lab1_hello.png")
print("wrote assets/output/lab1_hello.png")
```

## Checkpoint

You can call Slang from Python and see live pixels. Next: Lab 2 (autodiff) or Lab 4 (train BRDF).

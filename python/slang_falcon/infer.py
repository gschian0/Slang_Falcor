"""Infer / visualize teacher vs MLP BRDF slice.

Usage:
    python -m slang_falcon.infer --weights assets/weights/brdf_mlp.bin --out assets/output/brdf_compare.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from slang_falcon import OUTPUT_DIR, WEIGHTS_DIR
from slang_falcon.network import numpy_mlp_forward
from slang_falcon.train_brdf import _disney_cpu, _pack_features
from slang_falcon.weights import load_weights


def render_compare_cpu(weights_path: Path, width: int = 256, height: int = 256) -> np.ndarray:
    """Return Hx(3W)x3 uint8 strip: teacher | mlp | abs-diff."""
    mlp = load_weights(weights_path)
    N = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    albedo = np.array([0.8, 0.15, 0.1], dtype=np.float32)
    V = np.array([0.2, 0.3, 0.9], dtype=np.float32)
    V = V / np.linalg.norm(V)

    teacher = np.zeros((height, width, 3), dtype=np.float32)
    pred = np.zeros_like(teacher)
    for y in range(height):
        for x in range(width):
            ndotl = (x + 0.5) / width
            rough = 0.05 + 0.9 * ((y + 0.5) / height)
            L = np.array(
                [np.sqrt(max(0.0, 1.0 - ndotl * ndotl)), 0.0, ndotl], dtype=np.float32
            )
            feat = _pack_features(L, V, N, rough)
            teacher[y, x] = _disney_cpu(albedo, L, V, N, rough)
            pred[y, x] = numpy_mlp_forward(feat, mlp)

    diff = np.abs(teacher - pred) * 4.0

    def tonemap(img: np.ndarray) -> np.ndarray:
        t = img / (img + 1.0)
        return np.clip(t * 255.0, 0, 255).astype(np.uint8)

    strip = np.concatenate([tonemap(teacher), tonemap(pred), tonemap(diff)], axis=1)
    return strip


def render_compare_slangpy(weights_path: Path, width: int = 256, height: int = 256) -> np.ndarray:
    import slangpy as spy

    from slang_falcon.device import get_device, load_module
    from slang_falcon.network import BrdfNetwork

    device = get_device()
    train_mod = load_module("train_brdf")
    network = BrdfNetwork(train_mod, device)
    network.import_weights(weights_path)

    res = spy.int2(width, height)
    panels = []
    for mode in (0, 1, 2):
        out = spy.Tensor.empty(device, shape=(height, width), dtype=spy.float3)
        train_mod.render_slice(
            pixel=spy.call_id(),
            resolution=res,
            network=network.slang,
            mode=mode,
            _result=out,
        )
        panels.append(out.to_numpy())

    def tonemap(img: np.ndarray) -> np.ndarray:
        t = img / (img + 1.0)
        return np.clip(t * 255.0, 0, 255).astype(np.uint8)

    return np.concatenate([tonemap(p) for p in panels], axis=1)


def infer(
    weights: Path,
    out: Path,
    width: int = 256,
    height: int = 256,
    backend: str = "auto",
) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if backend == "auto":
        try:
            import slangpy  # noqa: F401

            backend = "slangpy"
        except ImportError:
            backend = "numpy"

    if backend == "slangpy":
        try:
            strip = render_compare_slangpy(weights, width, height)
        except Exception as exc:  # noqa: BLE001
            print(f"slangpy infer failed ({exc}); using numpy")
            strip = render_compare_cpu(weights, width, height)
    else:
        strip = render_compare_cpu(weights, width, height)

    Image.fromarray(strip, mode="RGB").save(out)
    print(f"Wrote image -> {out}")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render teacher | MLP | diff strip")
    p.add_argument("--weights", type=Path, default=WEIGHTS_DIR / "brdf_mlp.bin")
    p.add_argument("--out", type=Path, default=OUTPUT_DIR / "brdf_compare.png")
    p.add_argument("--width", type=int, default=256)
    p.add_argument("--height", type=int, default=256)
    p.add_argument("--backend", choices=("auto", "slangpy", "numpy"), default="auto")
    args = p.parse_args(argv)
    if not args.weights.exists():
        raise SystemExit(f"weights not found: {args.weights} (run train_brdf first)")
    infer(args.weights, args.out, args.width, args.height, args.backend)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

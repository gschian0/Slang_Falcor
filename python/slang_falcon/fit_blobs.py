"""Fit isotropic 2D Gaussians to a procedural target (afternoon-style loop).

Usage:
    python -m slang_falcon.fit_blobs --steps 400 --out assets/output/fit_blobs.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from slang_falcon import OUTPUT_DIR


def _target(h: int, w: int) -> np.ndarray:
    """Two soft blobs — matches the live NG02/NG03 teaching target."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    uv_x = (xs + 0.5) / float(w)
    uv_y = (ys + 0.5) / float(h)
    p = np.stack([uv_x * 2.0 - 1.0, uv_y * 2.0 - 1.0], axis=-1)
    d0 = np.linalg.norm(p - np.array([-0.15, 0.1], dtype=np.float32), axis=-1)
    d1 = np.linalg.norm(p - np.array([0.35, -0.2], dtype=np.float32), axis=-1)
    b0 = np.exp(-d0 * d0 * 14.0)
    b1 = np.exp(-d1 * d1 * 10.0)
    rgb = np.stack(
        [
            0.9 * b0 + 0.2 * b1,
            0.35 * b0 + 0.7 * b1,
            0.2 + 0.5 * b0,
        ],
        axis=-1,
    ).astype(np.float32)
    return np.clip(rgb, 0.0, 1.0)


def _render(params: np.ndarray, h: int, w: int) -> np.ndarray:
    """params: (N, 6) = cx, cy, sigma, r, g, b in UV/[0,1] space."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    uv_x = (xs + 0.5) / float(w)
    uv_y = (ys + 0.5) / float(h)
    img = np.zeros((h, w, 3), dtype=np.float32)
    for i in range(params.shape[0]):
        cx, cy, sigma, r, g, b = params[i]
        sigma = max(float(sigma), 1e-3)
        dx = (uv_x - cx) / sigma
        dy = (uv_y - cy) / sigma
        wgt = np.exp(-(dx * dx + dy * dy))
        img[..., 0] += r * wgt
        img[..., 1] += g * wgt
        img[..., 2] += b * wgt
    return np.clip(img, 0.0, 1.0)


def _grads(params: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, float]:
    h, w, _ = target.shape
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    uv_x = (xs + 0.5) / float(w)
    uv_y = (ys + 0.5) / float(h)
    pred = _render(params, h, w)
    err = pred - target
    loss = float(np.mean(err * err))
    g = np.zeros_like(params)
    # dL/dpred = 2*err / (H*W*3) for mean; use 2*err/(H*W) per channel mean
    scale = 2.0 / float(h * w)
    for i in range(params.shape[0]):
        cx, cy, sigma, r, gch, bch = params[i]
        sigma = max(float(sigma), 1e-3)
        dx = (uv_x - cx) / sigma
        dy = (uv_y - cy) / sigma
        wgt = np.exp(-(dx * dx + dy * dy))
        # color grads
        g[i, 3] = scale * np.sum(err[..., 0] * wgt)
        g[i, 4] = scale * np.sum(err[..., 1] * wgt)
        g[i, 5] = scale * np.sum(err[..., 2] * wgt)
        # spatial / sigma via chain rule on wgt
        # dw/dcx = wgt * 2*dx/sigma, dw/dcy = wgt * 2*dy/sigma
        # dw/dsigma = wgt * 2*(dx^2+dy^2)/sigma
        dw_dcx = wgt * (2.0 * dx / sigma)
        dw_dcy = wgt * (2.0 * dy / sigma)
        dw_ds = wgt * (2.0 * (dx * dx + dy * dy) / sigma)
        col = np.array([r, gch, bch], dtype=np.float32)
        for c in range(3):
            g[i, 0] += scale * np.sum(err[..., c] * col[c] * dw_dcx)
            g[i, 1] += scale * np.sum(err[..., c] * col[c] * dw_dcy)
            g[i, 2] += scale * np.sum(err[..., c] * col[c] * dw_ds)
    return g, loss


def fit_blobs(
    steps: int = 400,
    blobs: int = 8,
    width: int = 64,
    height: int = 64,
    lr: float = 0.05,
    seed: int = 0,
    out: Path | None = None,
    log_every: int = 50,
) -> list[float]:
    rng = np.random.default_rng(seed)
    target = _target(height, width)
    # cx, cy, sigma, r, g, b
    params = np.zeros((blobs, 6), dtype=np.float32)
    params[:, 0:2] = rng.random((blobs, 2), dtype=np.float32)
    params[:, 2] = 0.12 + 0.2 * rng.random(blobs, dtype=np.float32)
    params[:, 3:6] = rng.random((blobs, 3), dtype=np.float32)

    m = np.zeros_like(params)
    v = np.zeros_like(params)
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    losses: list[float] = []

    for step in range(1, steps + 1):
        g, loss = _grads(params, target)
        m = beta1 * m + (1.0 - beta1) * g
        v = beta2 * v + (1.0 - beta2) * (g * g)
        mhat = m / (1.0 - beta1**step)
        vhat = v / (1.0 - beta2**step)
        params -= lr * mhat / (np.sqrt(vhat) + eps)
        # Project to sane ranges
        params[:, 0:2] = np.clip(params[:, 0:2], -0.2, 1.2)
        params[:, 2] = np.clip(params[:, 2], 0.03, 0.6)
        params[:, 3:6] = np.clip(params[:, 3:6], 0.0, 1.5)

        if step % log_every == 0 or step == 1 or step == steps:
            losses.append(loss)
            print(f"step {step:5d}  loss={loss:.6f}")

    pred = _render(params, height, width)
    strip = np.concatenate([target, pred, np.clip(4.0 * np.abs(pred - target), 0, 1)], axis=1)
    out = Path(out) if out else OUTPUT_DIR / "fit_blobs.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((strip * 255.0).astype(np.uint8)).save(out)
    print(f"Wrote {out}")
    return losses


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fit 2D Gaussians to a procedural image (NumPy Adam)")
    p.add_argument("--steps", type=int, default=400)
    p.add_argument("--blobs", type=int, default=8)
    p.add_argument("--size", type=int, default=64, help="Square resolution")
    p.add_argument("--lr", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--log-every", type=int, default=50)
    args = p.parse_args(argv)
    losses = fit_blobs(
        steps=args.steps,
        blobs=args.blobs,
        width=args.size,
        height=args.size,
        lr=args.lr,
        seed=args.seed,
        out=args.out,
        log_every=args.log_every,
    )
    if len(losses) >= 2 and losses[-1] >= losses[0]:
        print("warning: loss did not decrease (try more steps / different seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

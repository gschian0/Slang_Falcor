"""Train a Disney-BRDF teacher with a tiny MLP and export SFMLP001 weights.

Usage:
    python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from slang_falcon import WEIGHTS_DIR
from slang_falcon.weights import LayerWeights, save_weights


def _train_slangpy(
    steps: int,
    batch_size: int,
    lr: float,
    seed: int,
    out: Path,
    log_every: int,
) -> list[float]:
    import slangpy as spy

    from slang_falcon.device import get_device, load_module
    from slang_falcon.network import BrdfNetwork

    np.random.seed(seed)
    device = get_device()
    # train_brdf.slang is self-contained (MLP + Disney + kernels)
    train_mod = load_module("train_brdf")
    network = BrdfNetwork(train_mod, device)

    print("Compiling train kernels (first step may take a while)...")
    losses: list[float] = []
    opt_iter = 0

    for step in range(steps):
        seeds = np.random.randint(0, 2**31 - 1, size=batch_size, dtype=np.uint32)
        # Dispatch one sample per seed via grid / vectorized call
        train_mod.train_sample(seed=seeds, network=network.slang)
        opt_iter += 1
        network.optimize(lr, opt_iter)

        if step % log_every == 0 or step == steps - 1:
            loss_seeds = np.random.randint(0, 2**31 - 1, size=256, dtype=np.uint32)
            # Evaluate mean channel loss over a probe batch
            probe = train_mod.loss_sample(seed=loss_seeds, network=network.slang)
            arr = probe.to_numpy() if hasattr(probe, "to_numpy") else np.asarray(probe)
            mean_loss = float(np.mean(arr))
            losses.append(mean_loss)
            print(f"step {step:5d}  loss={mean_loss:.6f}")

    network.export_weights(out)
    print(f"Wrote weights -> {out}")
    return losses


def _disney_cpu(
    albedo: np.ndarray,
    L: np.ndarray,
    V: np.ndarray,
    N: np.ndarray,
    roughness: float,
    metallic: float = 0.0,
    specular: float = 0.5,
) -> np.ndarray:
    """Minimal Disney BRDF + cosine (CPU teacher for fallback training)."""
    pi = np.pi
    NdotL = float(np.dot(N, L))
    NdotV = float(np.dot(N, V))
    if NdotL < 0.0 or NdotV < 0.0:
        return np.zeros(3, dtype=np.float32)
    H = L + V
    H = H / (np.linalg.norm(H) + 1e-8)
    NdotH = float(np.dot(N, H))
    LdotH = float(np.dot(L, H))

    def schlick(u: float) -> float:
        m = max(min(1.0 - u, 1.0), 0.0)
        m2 = m * m
        return m2 * m2 * m

    Cdlin = albedo
    Cspec0 = (1.0 - metallic) * specular * 0.08 + metallic * Cdlin
    FL, FV = schlick(NdotL), schlick(NdotV)
    Fd90 = 0.5 + 2.0 * LdotH * LdotH * roughness
    Fd = (1.0 + (Fd90 - 1.0) * FL) * (1.0 + (Fd90 - 1.0) * FV)
    a = max(roughness * roughness, 1e-4)
    a2 = a * a
    t = 1.0 + (a2 - 1.0) * NdotH * NdotH
    Ds = a2 / (pi * t * t)
    FH = schlick(LdotH)
    Fs = Cspec0 + (1.0 - Cspec0) * FH

    def smith(nd: float) -> float:
        aa = a * a
        bb = nd * nd
        return 1.0 / (nd + np.sqrt(aa + bb - aa * bb))

    Gs = smith(NdotL) * smith(NdotV)
    diff = (1.0 / pi) * Fd * Cdlin * (1.0 - metallic)
    spec = Gs * Fs * Ds
    return ((diff + spec) * max(NdotL, 0.0)).astype(np.float32)


def _pack_features(L: np.ndarray, V: np.ndarray, N: np.ndarray, roughness: float) -> np.ndarray:
    H = L + V
    H = H / (np.linalg.norm(H) + 1e-8)
    return np.array(
        [
            max(float(np.dot(N, L)), 0.0),
            max(float(np.dot(N, V)), 0.0),
            max(float(np.dot(N, H)), 0.0),
            max(float(np.dot(L, H)), 0.0),
            float(np.clip(roughness, 0.0, 1.0)),
        ],
        dtype=np.float32,
    )


def _sample_hemisphere(rng: np.random.Generator) -> np.ndarray:
    u1, u2 = rng.random(), rng.random()
    r = np.sqrt(u1)
    phi = 2.0 * np.pi * u2
    return np.array([r * np.cos(phi), r * np.sin(phi), np.sqrt(max(0.0, 1.0 - u1))], dtype=np.float32)


def _softplus(x: np.ndarray) -> np.ndarray:
    return np.log1p(np.exp(np.clip(x, -80, 80)))


def _softplus_grad(y: np.ndarray) -> np.ndarray:
    # d/dx softplus = sigmoid
    return 1.0 / (1.0 + np.exp(-np.clip(y, -80, 80)))


def train_numpy(
    steps: int,
    batch_size: int,
    lr: float,
    seed: int,
    out: Path,
    log_every: int,
) -> list[float]:
    """CPU autodiff MLP training against Disney teacher (CI / no-GPU fallback)."""
    rng = np.random.default_rng(seed)
    sizes = [(5, 32), (32, 32), (32, 3)]
    layers: list[dict] = []
    for inp, out_n in sizes:
        scale = 1.0 / np.sqrt(inp)
        layers.append(
            {
                "W": rng.uniform(-scale, scale, (out_n, inp)).astype(np.float32),
                "b": np.zeros(out_n, dtype=np.float32),
                "mW": np.zeros((out_n, inp), dtype=np.float32),
                "mb": np.zeros(out_n, dtype=np.float32),
                "vW": np.zeros((out_n, inp), dtype=np.float32),
                "vb": np.zeros(out_n, dtype=np.float32),
            }
        )

    albedo = np.array([0.8, 0.15, 0.1], dtype=np.float32)
    N = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    losses: list[float] = []
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    t = 0

    def forward(feat: np.ndarray):
        xs = [feat]
        preacts = []
        x = feat
        for i, layer in enumerate(layers):
            z = layer["W"] @ x + layer["b"]
            preacts.append(z)
            if i < len(layers) - 1:
                x = np.maximum(z, 0.0)
            else:
                x = _softplus(z)
            xs.append(x)
        return xs, preacts

    for step in range(steps):
        gradW = [np.zeros_like(L["W"]) for L in layers]
        gradb = [np.zeros_like(L["b"]) for L in layers]
        batch_loss = 0.0
        for _ in range(batch_size):
            Lvec = _sample_hemisphere(rng)
            Vvec = _sample_hemisphere(rng)
            rough = 0.05 + 0.9 * float(rng.random())
            feat = _pack_features(Lvec, Vvec, N, rough)
            teacher = _disney_cpu(albedo, Lvec, Vvec, N, rough)
            xs, preacts = forward(feat)
            pred = xs[-1]
            err = pred - teacher
            batch_loss += float(np.mean(err * err))
            # dL/dpred = 2/3 * err for mean over channels... use 2*err
            dout = 2.0 * err
            # softplus
            dz = dout * _softplus_grad(preacts[-1])
            for i in reversed(range(len(layers))):
                x_in = xs[i]
                gradW[i] += np.outer(dz, x_in)
                gradb[i] += dz
                if i > 0:
                    dx = layers[i]["W"].T @ dz
                    # ReLU
                    dz = dx * (preacts[i - 1] > 0).astype(np.float32)

        scale = 1.0 / batch_size
        t += 1
        for i, layer in enumerate(layers):
            gW = gradW[i] * scale
            gb = gradb[i] * scale
            layer["mW"] = beta1 * layer["mW"] + (1 - beta1) * gW
            layer["mb"] = beta1 * layer["mb"] + (1 - beta1) * gb
            layer["vW"] = beta2 * layer["vW"] + (1 - beta2) * (gW * gW)
            layer["vb"] = beta2 * layer["vb"] + (1 - beta2) * (gb * gb)
            mW = layer["mW"] / (1 - beta1**t)
            mb = layer["mb"] / (1 - beta1**t)
            vW = layer["vW"] / (1 - beta2**t)
            vb = layer["vb"] / (1 - beta2**t)
            layer["W"] -= lr * mW / (np.sqrt(vW) + eps)
            layer["b"] -= lr * mb / (np.sqrt(vb) + eps)

        if step % log_every == 0 or step == steps - 1:
            mean_loss = batch_loss / batch_size
            losses.append(mean_loss)
            print(f"step {step:5d}  loss={mean_loss:.6f}  [numpy]")

    packed = [
        LayerWeights(inp, out_n, layers[i]["b"].copy(), layers[i]["W"].copy())
        for i, (inp, out_n) in enumerate(sizes)
    ]
    save_weights(out, packed)
    print(f"Wrote weights -> {out}")
    return losses


def train(
    steps: int = 200,
    batch_size: int = 64,
    lr: float = 1e-3,
    seed: int = 0,
    out: Path | None = None,
    backend: str = "auto",
    log_every: int = 20,
) -> list[float]:
    out = Path(out) if out else WEIGHTS_DIR / "brdf_mlp.bin"
    out.parent.mkdir(parents=True, exist_ok=True)

    if backend == "auto":
        try:
            import slangpy  # noqa: F401

            backend = "slangpy"
        except ImportError:
            print("slangpy not installed - using numpy backend", file=sys.stderr)
            backend = "numpy"

    if backend == "slangpy":
        try:
            return _train_slangpy(steps, batch_size, lr, seed, out, log_every)
        except Exception as exc:  # noqa: BLE001
            print(f"slangpy training failed ({exc}); falling back to numpy", file=sys.stderr)
            return train_numpy(steps, batch_size, lr, seed, out, log_every)
    if backend == "numpy":
        return train_numpy(steps, batch_size, lr, seed, out, log_every)
    raise ValueError(f"unknown backend {backend}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Train BRDF MLP (Disney teacher)")
    p.add_argument("--steps", type=int, default=200)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", type=Path, default=WEIGHTS_DIR / "brdf_mlp.bin")
    p.add_argument("--backend", choices=("auto", "slangpy", "numpy"), default="auto")
    p.add_argument("--log-every", type=int, default=20)
    args = p.parse_args(argv)
    train(
        steps=args.steps,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
        out=args.out,
        backend=args.backend,
        log_every=args.log_every,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

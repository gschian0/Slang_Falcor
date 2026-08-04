"""Smoke tests: training reduces loss; end-to-end image output."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from slang_falcon.infer import infer
from slang_falcon.train_brdf import train
from slang_falcon.weights import MAGIC, load_weights


def test_weight_roundtrip(tmp_path: Path):
    from slang_falcon.weights import LayerWeights, save_weights

    layers = [
        LayerWeights(5, 32, np.zeros(32, np.float32), np.ones((32, 5), np.float32) * 0.01),
        LayerWeights(32, 32, np.zeros(32, np.float32), np.eye(32, dtype=np.float32) * 0.01),
        LayerWeights(32, 3, np.zeros(3, np.float32), np.ones((3, 32), np.float32) * 0.01),
    ]
    path = tmp_path / "t.bin"
    save_weights(path, layers)
    raw = path.read_bytes()
    assert raw[:8] == MAGIC
    loaded = load_weights(path)
    assert len(loaded.layers) == 3
    np.testing.assert_allclose(loaded.layers[0].weights, layers[0].weights)


def test_training_reduces_loss(tmp_path: Path):
    out = tmp_path / "brdf_mlp.bin"
    losses = train(
        steps=40,
        batch_size=32,
        lr=2e-3,
        seed=42,
        out=out,
        backend="numpy",
        log_every=10,
    )
    assert out.exists()
    assert len(losses) >= 2
    # Allow a little noise but require clear improvement from first logged to last
    assert losses[-1] < losses[0] * 0.85, f"loss did not drop enough: {losses}"


def test_infer_writes_image(tmp_path: Path):
    weights = tmp_path / "brdf_mlp.bin"
    image_path = tmp_path / "compare.png"
    train(steps=20, batch_size=16, seed=1, out=weights, backend="numpy", log_every=20)
    infer(weights, image_path, width=64, height=64, backend="numpy")
    assert image_path.exists()
    img = np.array(Image.open(image_path))
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.shape[0] == 64
    assert img.shape[1] == 64 * 3  # teacher | mlp | diff

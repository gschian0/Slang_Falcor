"""Binary weight export / import for Phase 1 → Phase 2 / WebGPU.

Format (little-endian), documented in docs/weight_format.md:

    magic:     8 bytes  b"SFMLP001"
    version:   u32      = 1
    n_layers:  u32
    for each layer:
        inputs:  u32
        outputs: u32
    for each layer:
        biases:  outputs * f32
        weights: outputs * inputs * f32   (row-major: neuron major, input minor)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

MAGIC = b"SFMLP001"
VERSION = 1


@dataclass
class LayerWeights:
    inputs: int
    outputs: int
    biases: np.ndarray  # (outputs,)
    weights: np.ndarray  # (outputs, inputs)

    def validate(self) -> None:
        if self.biases.shape != (self.outputs,):
            raise ValueError(f"bias shape {self.biases.shape} != ({self.outputs},)")
        if self.weights.shape != (self.outputs, self.inputs):
            raise ValueError(
                f"weight shape {self.weights.shape} != ({self.outputs}, {self.inputs})"
            )


@dataclass
class MlpWeights:
    layers: list[LayerWeights]

    @property
    def layer_sizes(self) -> list[tuple[int, int]]:
        return [(layer.inputs, layer.outputs) for layer in self.layers]


def save_weights(path: Path | str, layers: Sequence[LayerWeights]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    for layer in layers:
        layer.validate()

    with path.open("wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<II", VERSION, len(layers)))
        for layer in layers:
            f.write(struct.pack("<II", layer.inputs, layer.outputs))
        for layer in layers:
            f.write(np.asarray(layer.biases, dtype=np.float32).tobytes())
            f.write(np.asarray(layer.weights, dtype=np.float32).ravel(order="C").tobytes())


def load_weights(path: Path | str) -> MlpWeights:
    path = Path(path)
    with path.open("rb") as f:
        magic = f.read(8)
        if magic != MAGIC:
            raise ValueError(f"bad magic {magic!r}, expected {MAGIC!r}")
        version, n_layers = struct.unpack("<II", f.read(8))
        if version != VERSION:
            raise ValueError(f"unsupported weight version {version}")
        shapes: list[tuple[int, int]] = []
        for _ in range(n_layers):
            inputs, outputs = struct.unpack("<II", f.read(8))
            shapes.append((inputs, outputs))
        layers: list[LayerWeights] = []
        for inputs, outputs in shapes:
            biases = np.frombuffer(f.read(outputs * 4), dtype=np.float32).copy()
            weights = np.frombuffer(
                f.read(outputs * inputs * 4), dtype=np.float32
            ).copy().reshape((outputs, inputs))
            layers.append(LayerWeights(inputs, outputs, biases, weights))
    return MlpWeights(layers)


def flatten_for_native(weights: MlpWeights) -> np.ndarray:
    """Concatenate all biases then weights per layer (same order as file body)."""
    chunks: list[np.ndarray] = []
    for layer in weights.layers:
        chunks.append(layer.biases.astype(np.float32).ravel())
        chunks.append(layer.weights.astype(np.float32).ravel(order="C"))
    return np.concatenate(chunks)

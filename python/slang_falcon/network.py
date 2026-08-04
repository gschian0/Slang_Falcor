"""Python-side BrdfMLP wrapping SlangPy InstanceLists + weight I/O."""

from __future__ import annotations

from typing import Any

import numpy as np

from slang_falcon import BRDF_LAYER_SIZES
from slang_falcon.weights import LayerWeights, load_weights, save_weights


def _make_linear_layer(module: Any, inputs: int, outputs: int, device: Any):
    import slangpy as spy

    class LinearLayer(spy.InstanceList):
        def __init__(self):
            super().__init__(module[f"LinearLayer<{inputs}, {outputs}>"])
            self.inputs = inputs
            self.outputs = outputs
            self._module = module
            scale = 1.0 / np.sqrt(inputs)
            self.biases = spy.Tensor.from_numpy(
                device, np.zeros(outputs, dtype=np.float32)
            )
            self.weights = spy.Tensor.from_numpy(
                device,
                np.random.uniform(-scale, scale, (outputs, inputs)).astype(np.float32),
            )
            self.biases_grad = spy.Tensor.zeros_like(self.biases)
            self.weights_grad = spy.Tensor.zeros_like(self.weights)
            self.m_biases = spy.Tensor.zeros_like(self.biases)
            self.m_weights = spy.Tensor.zeros_like(self.weights)
            self.v_biases = spy.Tensor.zeros_like(self.biases)
            self.v_weights = spy.Tensor.zeros_like(self.weights)

        def optimize(self, learning_rate: float, iteration: int) -> None:
            self._module.optimizer_step(
                self.biases,
                self.biases_grad,
                self.m_biases,
                self.v_biases,
                learning_rate,
                iteration,
            )
            self._module.optimizer_step(
                self.weights,
                self.weights_grad,
                self.m_weights,
                self.v_weights,
                learning_rate,
                iteration,
            )

        def to_layer_weights(self) -> LayerWeights:
            return LayerWeights(
                self.inputs,
                self.outputs,
                self.biases.to_numpy().astype(np.float32),
                self.weights.to_numpy().astype(np.float32),
            )

        def load_layer_weights(self, layer: LayerWeights) -> None:
            layer.validate()
            if (layer.inputs, layer.outputs) != (self.inputs, self.outputs):
                raise ValueError("layer shape mismatch")
            self.biases = spy.Tensor.from_numpy(device, layer.biases.astype(np.float32))
            self.weights = spy.Tensor.from_numpy(
                device, layer.weights.astype(np.float32)
            )
            self.biases_grad = spy.Tensor.zeros_like(self.biases)
            self.weights_grad = spy.Tensor.zeros_like(self.weights)

    return LinearLayer()


class BrdfNetwork:
    """Matches slang `BrdfMLP`."""

    def __init__(self, mlp_module: Any, device: Any):
        import slangpy as spy

        self._module = mlp_module
        self._device = device
        sizes = BRDF_LAYER_SIZES
        self.layer0 = _make_linear_layer(mlp_module, *sizes[0], device)
        self.layer1 = _make_linear_layer(mlp_module, *sizes[1], device)
        self.layer2 = _make_linear_layer(mlp_module, *sizes[2], device)

        class BrdfMLP(spy.InstanceList):
            def __init__(self_inner):
                super().__init__(mlp_module["BrdfMLP"])
                self_inner.layer0 = self.layer0
                self_inner.layer1 = self.layer1
                self_inner.layer2 = self.layer2

        self._inst = BrdfMLP()

    @property
    def slang(self):
        return self._inst

    def optimize(self, learning_rate: float, iteration: int) -> None:
        self.layer0.optimize(learning_rate, iteration)
        self.layer1.optimize(learning_rate, iteration)
        self.layer2.optimize(learning_rate, iteration)

    def export_weights(self, path) -> None:
        save_weights(
            path,
            [
                self.layer0.to_layer_weights(),
                self.layer1.to_layer_weights(),
                self.layer2.to_layer_weights(),
            ],
        )

    def import_weights(self, path) -> None:
        packed = load_weights(path)
        if len(packed.layers) != 3:
            raise ValueError(f"expected 3 layers, got {len(packed.layers)}")
        self.layer0.load_layer_weights(packed.layers[0])
        self.layer1.load_layer_weights(packed.layers[1])
        self.layer2.load_layer_weights(packed.layers[2])
        self._inst.layer0 = self.layer0
        self._inst.layer1 = self.layer1
        self._inst.layer2 = self.layer2


def numpy_mlp_forward(features: np.ndarray, weights) -> np.ndarray:
    """CPU reference forward (for WebGPU parity / tests without GPU)."""
    x = features.astype(np.float32)
    for i, layer in enumerate(weights.layers):
        x = layer.weights @ x + layer.biases
        if i < len(weights.layers) - 1:
            x = np.maximum(x, 0.0)
        else:
            x = np.log1p(np.exp(np.clip(x, -80, 80)))  # softplus
    return x

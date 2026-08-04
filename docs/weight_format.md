# Weight export format (`SFMLP001`)

Phase 1 writes a portable binary that Phase 2 (Falcor) and Phase 3 (WebGPU) load.

## Layout (little-endian)

| Field | Type | Notes |
|-------|------|--------|
| magic | 8 bytes | ASCII `SFMLP001` |
| version | `u32` | Currently `1` |
| n_layers | `u32` | For default BRDF MLP: `3` |
| layer shapes | `n_layers × (u32 inputs, u32 outputs)` | e.g. `(5,32), (32,32), (32,3)` |
| layer payloads | per layer, in order | see below |

### Per-layer payload

1. **biases** — `outputs` × `float32`
2. **weights** — `outputs × inputs` × `float32`, **row-major**  
   Index: `weights[row * inputs + col]` where `row` is output neuron, `col` is input.

Forward for each layer:

```
y[row] = biases[row] + sum_col weights[row, col] * x[col]
```

Hidden layers use **ReLU**. The final layer uses **softplus** so RGB stays non-negative.

## Default BRDF MLP

| Layer | Inputs | Outputs | Activation |
|-------|--------|---------|------------|
| 0 | 5 | 32 | ReLU |
| 1 | 32 | 32 | ReLU |
| 2 | 32 | 3 | softplus |

### Input features (order)

Matches `disney_brdf.pack_brdf_features`:

0. `N·L` (saturated)
1. `N·V`
2. `N·H`
3. `L·H`
4. `roughness`

### Output

Linear RGB approximation of Disney BRDF × `max(N·L, 0)` for the fixed lab material.

## Python API

```python
from slang_falcon.weights import load_weights, save_weights, LayerWeights

w = load_weights("assets/weights/brdf_mlp.bin")
# w.layers[i].biases, w.layers[i].weights
```

## Native (Phase 2) load sketch

```cpp
// See native/src/WeightLoader.cpp
// 1. Verify magic SFMLP001
// 2. Read shapes → allocate bias/weight buffers
// 3. Upload to ByteAddressBuffer for InferenceMLP / scalar fallback
```

## WebGPU (Phase 3)

`web/demos/brdf_compare.js` parses the same binary with `DataView` and runs the
float MLP in WGSL compute (no CoopVec).

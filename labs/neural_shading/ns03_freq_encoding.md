# NS03 — Frequency encoding

**Job:** compare raw UV → tiny net vs sin/cos-encoded UV → same-width net.

**Source post:** [How to Get Started with Neural Shading](https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/) (frequency encoding + leaky ReLU tips)

## Run

```powershell
python -m slang_falcon.live --lesson neural_shading/ns03_freq_encoding
```

- **Left:** `2→6→3` on raw UV (struggles with high-frequency target)
- **Right:** `4→6→3` on `[sin u, cos u, sin v, cos v]` with leaky ReLU
- Reddish tint: absolute error vs a ringing target pattern

Demo weights are illustrative — not trained exports.

## Idea

Small networks need help representing fine detail. Encoding coordinates as sines/cosines of a few frequencies gives the net high-frequency basis functions without widening the hidden layer much.

## Try

1. Change `TAU` multiples in `encode_uv` (2×, 4×).
2. Swap leaky ReLU for plain ReLU in `mlp4_rgb`.
3. Compare to texture-fit afternoon lesson `neural_gfx_afternoon/ng04_tiny_mlp_fit`.

Shader: `shaders/ns03_freq_encoding.slang`.

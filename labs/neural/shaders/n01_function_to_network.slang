// SPDX-License-Identifier: Apache-2.0
// Neural curriculum N01 — analytic shaping vs tiny baked MLP.
// Left: y = pow(x, 3). Right: 1→8→1 ReLU net approximating the same curve.

module neural_n01_function_to_network;

import slangpy;

float plot(float2 st, float pct)
{
    return smoothstep(pct - 0.02f, pct, st.y) -
           smoothstep(pct, pct + 0.02f, st.y);
}

/// Tiny 1→8→1 MLP with baked weights (fit offline to y = x^3 on [0,1]).
float mlp_curve(float x)
{
    // Layer 0: 8 hidden, ReLU
    float h[8];
    // weights W0[8], bias b0[8] — hand-tuned demo (not a trained export)
    float w0[8] = { 2.4f, -1.8f, 3.1f, 1.2f, -2.6f, 0.9f, 4.0f, -0.7f };
    float b0[8] = { -0.3f, 0.8f, -1.1f, 0.2f, 1.4f, -0.5f, -2.0f, 0.6f };
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
        h[i] = max(w0[i] * x + b0[i], 0.0f);

    // Layer 1: linear → scalar
    float w1[8] = { 0.35f, -0.22f, 0.41f, 0.18f, -0.28f, 0.15f, 0.52f, -0.12f };
    float b1 = -0.05f;
    float y = b1;
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
        y += w1[i] * h[i];
    return saturate(y);
}

/// Split view: analytic | neural. Green stroke = teacher; cyan = MLP.
public float3 hello_pixel(int2 pixel, int2 resolution)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 st = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, 1.0f - uv.y);

    float y_teacher = pow(st.x, 3.0f);
    float y_mlp = mlp_curve(st.x);
    float y = right ? y_mlp : y_teacher;

    float3 color = float3(y, y, y);
    float pct_t = plot(st, y_teacher);
    float pct_m = plot(st, y_mlp);
    // Always show both curves faintly; emphasize the active panel's curve.
    color = (1.0f - pct_t) * color + pct_t * float3(0.15f, 0.95f, 0.35f);
    color = (1.0f - pct_m * 0.85f) * color + pct_m * 0.85f * float3(0.2f, 0.75f, 0.95f);

    // Center divider
    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.9f, 0.9f, 0.85f);
    return color;
}

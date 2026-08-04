// SPDX-License-Identifier: Apache-2.0
// Neural shading NS03 — frequency encoding helps tiny nets learn detail.
// Left: UV → MLP directly. Right: sin/cos encoded UV → same-width net (baked demo weights).
// Inspired by: https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/

module neural_shading_ns03_freq_encoding;

import slangpy;

static const float TAU = 6.28318530718f;

float3 mlp2_rgb(float2 x)
{
    float h[6];
    float w0a[6] = { 2.5f, -2.0f, 1.8f, -1.2f, 3.0f, 0.7f };
    float w0b[6] = { -1.5f, 2.2f, 0.9f, 2.8f, -0.6f, 1.4f };
    float b0[6] = { -0.2f, 0.4f, -0.5f, 0.1f, -0.8f, 0.3f };
    [ForceUnroll]
    for (int i = 0; i < 6; ++i)
        h[i] = max(w0a[i] * x.x + w0b[i] * x.y + b0[i], 0.0f);

    float3 o = float3(0.05f, 0.05f, 0.08f);
    float wr[6] = { 0.3f, -0.15f, 0.25f, 0.1f, -0.2f, 0.18f };
    float wg[6] = { 0.1f, 0.28f, -0.12f, 0.22f, 0.08f, -0.1f };
    float wb[6] = { 0.2f, 0.05f, 0.3f, -0.08f, 0.15f, 0.12f };
    [ForceUnroll]
    for (int i = 0; i < 6; ++i)
    {
        o.x += wr[i] * h[i];
        o.y += wg[i] * h[i];
        o.z += wb[i] * h[i];
    }
    return saturate(o);
}

float3 mlp4_rgb(float4 x)
{
    // 4→6→3 — frequency features in, same hidden width
    float h[6];
    float w0[6][4] = {
        { 1.8f, -1.2f, 0.9f, 0.4f },
        { -1.0f, 2.0f, -0.5f, 1.1f },
        { 0.7f, 0.6f, 1.5f, -1.3f },
        { -0.4f, 1.1f, 0.8f, 1.6f },
        { 2.2f, -0.3f, -1.0f, 0.5f },
        { 0.3f, -1.5f, 1.2f, 0.9f }
    };
    float b0[6] = { -0.3f, 0.2f, -0.4f, 0.1f, -0.6f, 0.25f };
    [ForceUnroll]
    for (int i = 0; i < 6; ++i)
    {
        float s = b0[i];
        [ForceUnroll]
        for (int j = 0; j < 4; ++j)
            s += w0[i][j] * x[j];
        h[i] = max(s, 0.1f * s); // leaky ReLU
    }

    float3 o = float3(0.04f, 0.04f, 0.06f);
    float wr[6] = { 0.35f, -0.12f, 0.28f, 0.15f, -0.18f, 0.22f };
    float wg[6] = { 0.12f, 0.3f, -0.1f, 0.2f, 0.14f, -0.08f };
    float wb[6] = { 0.25f, 0.08f, 0.32f, -0.1f, 0.18f, 0.16f };
    [ForceUnroll]
    for (int i = 0; i < 6; ++i)
    {
        o.x += wr[i] * h[i];
        o.y += wg[i] * h[i];
        o.z += wb[i] * h[i];
    }
    return saturate(o);
}

float4 encode_uv(float2 uv)
{
    return float4(
        sin(uv.x * TAU),
        cos(uv.x * TAU),
        sin(uv.y * TAU),
        cos(uv.y * TAU));
}

/// Target pattern for visual judgment (checker-ish rings).
float3 target_tex(float2 uv, float time)
{
    float2 p = uv * 2.0f - 1.0f;
    float r = length(p);
    float rings = 0.5f + 0.5f * cos(18.0f * r - time * 2.0f);
    float ang = atan2(p.y, p.x);
    float spokes = 0.5f + 0.5f * cos(6.0f * ang);
    float v = rings * spokes;
    return float3(v, 0.4f + 0.4f * uv.x, 0.5f + 0.3f * uv.y);
}

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 local = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);

    float3 tgt = target_tex(local, time);
    float3 pred = right ? mlp4_rgb(encode_uv(local)) : mlp2_rgb(local);

    // Show prediction; faint target outline via abs-diff darkening
    float err = length(pred - tgt);
    float3 color = lerp(pred, tgt, 0.15f);
    color = lerp(color, float3(1.0f, 0.3f, 0.2f), saturate(err) * 0.35f);

    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

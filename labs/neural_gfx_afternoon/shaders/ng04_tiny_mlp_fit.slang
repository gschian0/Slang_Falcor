// SPDX-License-Identifier: Apache-2.0
// Neural GFX afternoon NG04 — tiny MLP UV→RGB fit (baked stages vs target).
// Left: target procedural texture. Right: MLP prediction (weights morph with time toward a better fit).
// Inspired by: https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/

module neural_gfx_ng04_tiny_mlp_fit;

import slangpy;

static const float TAU = 6.28318530718f;

float3 target_tex(float2 uv)
{
    float2 p = uv * 2.0f - 1.0f;
    float r = length(p);
    float v = 0.5f + 0.5f * cos(10.0f * r) * cos(4.0f * atan2(p.y, p.x));
    return float3(v, 0.3f + 0.5f * uv.x, 0.4f + 0.4f * (1.0f - uv.y));
}

float3 mlp(float2 uv, float mixw)
{
    float4 enc = float4(sin(uv.x * TAU), cos(uv.x * TAU), sin(uv.y * TAU), cos(uv.y * TAU));
    // Two weight sets: early (bad) and late (better hand-tuned) — lerp by mixw
    float h[6];
    [ForceUnroll]
    for (int i = 0; i < 6; ++i)
    {
        float fi = float(i);
        float w_bad = 0.4f * sin(fi * 1.7f);
        float w_good = 0.9f * cos(fi * 0.9f + 0.3f);
        float w = lerp(w_bad, w_good, mixw);
        float s = -0.2f + w * enc.x + (0.5f - 0.1f * fi) * enc.y
                + (0.3f + 0.05f * fi) * enc.z + (-0.25f + 0.08f * fi) * enc.w;
        // late stage strengthens angular terms
        s += mixw * 0.35f * enc.z * cos(fi);
        h[i] = max(s, 0.1f * s);
    }

    float3 o = float3(0.05f, 0.08f, 0.1f);
    [ForceUnroll]
    for (int i = 0; i < 6; ++i)
    {
        float fi = float(i);
        o.x += (0.15f + 0.05f * fi) * h[i] * (0.5f + 0.5f * mixw);
        o.y += (0.12f + 0.03f * fi) * h[i];
        o.z += (0.1f + 0.04f * fi) * h[i];
    }
    return saturate(o);
}

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 local = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);

    float mixw = saturate(time / 7.0f);
    mixw = mixw * mixw * (3.0f - 2.0f * mixw);

    float3 color = right ? mlp(local, mixw) : target_tex(local);

    if (right && local.y > 0.94f)
        color = lerp(float3(0.15f, 0.15f, 0.18f), float3(0.35f, 0.75f, 0.95f), step(local.x, mixw));

    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

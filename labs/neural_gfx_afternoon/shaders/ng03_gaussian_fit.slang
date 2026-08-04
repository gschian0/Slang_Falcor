// SPDX-License-Identifier: Apache-2.0
// Neural GFX afternoon NG03 — 2D Gaussian image fit (animated “training” toward target).
// time acts as a fake iteration index: blobs lerp from random init → fitted params.
// Real optimize: python -m slang_falcon.fit_blobs
// Inspired by: https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/

module neural_gfx_ng03_gaussian_fit;

import slangpy;

float3 target_img(float2 uv)
{
    float2 p = uv * 2.0f - 1.0f;
    float d = length(p - float2(-0.15f, 0.1f));
    float blob = exp(-d * d * 14.0f);
    float d2 = length(p - float2(0.35f, -0.2f));
    float blob2 = exp(-d2 * d2 * 10.0f);
    return float3(0.9f * blob + 0.2f * blob2, 0.35f * blob + 0.7f * blob2, 0.2f + 0.5f * blob);
}

float3 splat(float2 uv, float2 c, float sigma, float3 col)
{
    float2 d = (uv - c) / max(sigma, 1e-3f);
    return col * exp(-dot(d, d));
}

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 local = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);

    // Progress 0→1 over ~8s, then hold.
    float t = saturate(time / 8.0f);
    t = t * t * (3.0f - 2.0f * t); // smoothstep

    // Init (random-ish) → fitted (matches target_img structure)
    float2 c0 = lerp(float2(0.2f, 0.8f), float2(0.425f, 0.45f), t); // maps to p≈(-0.15,0.1)
    float2 c1 = lerp(float2(0.9f, 0.2f), float2(0.675f, 0.6f), t);
    float s0 = lerp(0.35f, 0.19f, t);
    float s1 = lerp(0.4f, 0.22f, t);
    float3 col0 = lerp(float3(0.2f, 0.9f, 0.3f), float3(0.9f, 0.35f, 0.2f), t);
    float3 col1 = lerp(float3(0.9f, 0.2f, 0.8f), float3(0.25f, 0.7f, 0.85f), t);

    float3 pred = float3(0.05f, 0.05f, 0.07f);
    pred += splat(local, c0, s0, col0);
    pred += splat(local, c1, s1, col1);
    pred = saturate(pred);

    float3 color = right ? pred : target_img(local);

    // Progress bar
    if (local.y > 0.94f)
    {
        float bar = step(local.x, t);
        color = right ? lerp(float3(0.15f, 0.15f, 0.18f), float3(0.4f, 0.9f, 0.55f), bar)
                      : color;
    }

    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

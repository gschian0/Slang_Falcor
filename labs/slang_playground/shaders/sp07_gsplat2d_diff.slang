// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Differentiable 2D Splatter" intent (teaching viz).
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/gsplat2d-diff.slang
// Playground: https://shader-slang.org/slang-playground/
// Full demo trains blobs with Adam + bwd_diff against a URL target in-browser.
// Here: target | morphing blobs | |error| strip — same story without multi-buffer kernels.
// © shader-slang — adapted.

module sp07_gsplat2d_diff;

import slangpy;

float3 target_img(float2 uv)
{
    float2 p = uv * 2.0f - 1.0f;
    float d0 = length(p - float2(-0.2f, 0.15f));
    float d1 = length(p - float2(0.3f, -0.25f));
    float b0 = exp(-d0 * d0 * 12.0f);
    float b1 = exp(-d1 * d1 * 9.0f);
    return float3(0.85f * b0 + 0.15f * b1, 0.3f * b0 + 0.75f * b1, 0.2f + 0.55f * b0);
}

float3 splat(float2 uv, float2 c, float sigma, float3 col)
{
    float2 d = (uv - c) / max(sigma, 1e-3f);
    return col * exp(-dot(d, d));
}

/// Left target · middle fitting blobs · right abs error (time ≈ training step).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float third = 1.0f / 3.0f;
    int panel = uv.x < third ? 0 : (uv.x < 2.0f * third ? 1 : 2);
    float2 local = float2(frac(uv.x / third), uv.y);

    float t = saturate(time / 10.0f);
    t = t * t * (3.0f - 2.0f * t);

    float2 c0 = lerp(float2(0.15f, 0.8f), float2(0.4f, 0.425f), t);
    float2 c1 = lerp(float2(0.85f, 0.25f), float2(0.65f, 0.625f), t);
    float s0 = lerp(0.32f, 0.2f, t);
    float s1 = lerp(0.38f, 0.23f, t);
    float3 col0 = lerp(float3(0.2f, 0.9f, 0.4f), float3(0.85f, 0.3f, 0.2f), t);
    float3 col1 = lerp(float3(0.9f, 0.3f, 0.8f), float3(0.2f, 0.75f, 0.85f), t);

    float3 tgt = target_img(local);
    float3 pred = float3(0.05f, 0.05f, 0.07f);
    pred += splat(local, c0, s0, col0);
    pred += splat(local, c1, s1, col1);
    pred = saturate(pred);
    float3 err = abs(tgt - pred) * 2.5f;

    float3 color = panel == 0 ? tgt : (panel == 1 ? pred : err);

    if (local.y > 0.94f && panel == 1)
    {
        float bar = step(local.x, t);
        color = lerp(float3(0.12f, 0.12f, 0.14f), float3(0.35f, 0.85f, 0.5f), bar);
    }

    float x = uv.x;
    if (abs(x - third) < 1.5f / float(resolution.x) || abs(x - 2.0f * third) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

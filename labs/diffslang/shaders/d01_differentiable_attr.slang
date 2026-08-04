// SPDX-License-Identifier: Apache-2.0
// DiffSlang D01 — [Differentiable] as a first-class language feature.
// Teaching viz: primal loss landscape | |∂L/∂x| (gradient story).
// Inspired by: https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/

module diffslang_d01_differentiable_attr;

import slangpy;

/// Compiler can emit fwd/bwd forms for this. Real training uses bwd_diff / .bwds.
[Differentiable]
float field(float x, float y)
{
    return 0.6f * x * x + 0.35f * y * y + 0.2f * sin(4.0f * x) * cos(2.0f * y);
}

[Differentiable]
float loss(float x, float y, float target)
{
    float e = field(x, y) - target;
    return e * e;
}

float3 heat(float t)
{
    t = saturate(t);
    return float3(0.15f + 0.85f * t, 0.25f + 0.35f * t, 1.0f - 0.7f * t);
}

/// Left: L(x,y). Right: |∂L/∂x|. Target drifts with time (live uniform).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 p = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);
    float x = p.x * 2.0f - 1.0f;
    float y = (1.0f - p.y) * 2.0f - 1.0f;

    float target = 0.3f + 0.2f * sin(time * 0.6f);
    float L = loss(x, y, target);

    // Analytic ∂L/∂x matching autodiff for this tiny field (teaching mirror).
    float f = field(x, y);
    float e = f - target;
    float dfdx = 1.2f * x + 0.2f * 4.0f * cos(4.0f * x) * cos(2.0f * y);
    float dLdx = 2.0f * e * dfdx;

    float3 color = right ? heat(saturate(abs(dLdx) * 0.9f)) : heat(L * 2.2f);

    float cursor = 0.55f * sin(time * 0.45f);
    float tick = smoothstep(0.04f, 0.015f, abs(x - cursor));
    color = lerp(color, float3(0.95f, 0.9f, 0.35f), tick * 0.75f);

    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

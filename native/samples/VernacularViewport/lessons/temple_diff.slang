// SPDX-License-Identifier: Apache-2.0
// Temple school — differential / autodiff (2D live preview).
// Matches labs/diffslang + slang_playground/sp08 spirit: [Differentiable] field + analytic twin.
// Falcor 3D raster does not run bwd_diff this pass — Save here, preview in this window;
// 3D stays analytic VS/PS. Sister labs: diffslang/d01_differentiable_attr, neural/n03_autodiff_intuition.

module temple_diff;

import slangpy;

/// Compiler can emit fwd/bwd forms. Real training uses bwd_diff / .bwds (see labs/).
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

/// Left: L(x,y). Right: |∂L/∂x| (analytic mirror of autodiff). Target drifts with time.
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 p = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);
    float x = p.x * 2.0f - 1.0f;
    float y = (1.0f - p.y) * 2.0f - 1.0f;

    float target = 0.3f + 0.2f * sin(time * 0.6f);
    float L = loss(x, y, target);

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

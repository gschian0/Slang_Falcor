// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Automatic Differentiation" demo → image.
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/autodiff.slang
// Playground: https://shader-slang.org/slang-playground/
// Original prints fwd_diff / bwd_diff results; here we paint F, |∂F/∂x|, |∂F/∂y|.
// © shader-slang — adapted.

module sp08_autodiff;

import slangpy;

/// Same function as the playground print demo.
[Differentiable]
float sumOfSquares(float x, float y)
{
    return x * x + y * y;
}

float3 heat(float t)
{
    t = saturate(t);
    return float3(0.1f + 0.9f * t, 0.2f + 0.4f * t, 1.0f - 0.75f * t);
}

/// Left: F=x²+y² · mid: |∂F/∂x|=|2x| · right: |∂F/∂y|=|2y|.
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float third = 1.0f / 3.0f;
    int panel = uv.x < third ? 0 : (uv.x < 2.0f * third ? 1 : 2);
    float2 local = float2(frac(uv.x / third), uv.y);

    float x = local.x * 2.0f - 1.0f;
    float y = (1.0f - local.y) * 2.0f - 1.0f;
    // Drift the sample point the print demo used (2,3) scaled into view.
    float cx = 0.35f * sin(time * 0.4f);
    float cy = 0.25f * cos(time * 0.35f);
    x += cx;
    y += cy;

    float F = sumOfSquares(x, y);
    float dFdx = 2.0f * x; // matches fwd_diff seed on x / bwd_diff into x
    float dFdy = 2.0f * y;

    float3 color = panel == 0 ? heat(F * 0.35f)
                              : (panel == 1 ? heat(abs(dFdx) * 0.45f) : heat(abs(dFdy) * 0.45f));

    float tick = smoothstep(0.05f, 0.015f, length(float2(x - 0.0f, y - 0.0f)));
    color = lerp(color, float3(0.95f, 0.9f, 0.4f), tick * 0.35f);

    float xp = uv.x;
    if (abs(xp - third) < 1.5f / float(resolution.x) || abs(xp - 2.0f * third) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

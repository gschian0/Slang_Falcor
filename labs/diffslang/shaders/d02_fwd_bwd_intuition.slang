// SPDX-License-Identifier: Apache-2.0
// DiffSlang D02 — forward vs reverse intuition in pixels.
// Left: fwd-mode seed (directional derivative along a moving tangent).
// Right: bwd-mode idea — how much each (x,y) would pull a scalar loss.
// API reminder: fwd_diff(f) / bwd_diff(f) — see slang/train_brdf.slang for live bwd_diff.
// Inspired by: https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/

module diffslang_d02_fwd_bwd_intuition;

import slangpy;

[Differentiable]
float scalar_fn(float x, float y)
{
    // Smooth “ridge”: one output, two inputs — classic bwd vs fwd tradeoff.
    return sin(3.0f * x) * cos(2.0f * y) + 0.15f * (x * x + y * y);
}

float3 heat(float t)
{
    t = saturate(t);
    return float3(t, 0.3f + 0.4f * t, 1.0f - t);
}

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 p = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);
    float x = p.x * 2.0f - 1.0f;
    float y = (1.0f - p.y) * 2.0f - 1.0f;

    float f = scalar_fn(x, y);
    float dfdx = 3.0f * cos(3.0f * x) * cos(2.0f * y) + 0.3f * x;
    float dfdy = -2.0f * sin(3.0f * x) * sin(2.0f * y) + 0.3f * y;

    // Forward-mode intuition: pick a seed direction v, show ⟨∇f, v⟩ (JVP).
    float2 v = float2(cos(time * 0.7f), sin(time * 0.7f));
    float jvp = dfdx * v.x + dfdy * v.y;

    // Backward-mode intuition: seed dL/df = 1, show |∇f| (VJP into parameter space).
    float gmag = sqrt(dfdx * dfdx + dfdy * dfdy);

    float3 color;
    if (!right)
    {
        // Signed directional derivative → cool/warm
        float s = 0.5f + 0.5f * tanh(jvp * 1.5f);
        color = float3(s, 0.25f + 0.35f * s, 1.0f - s);
        // Arrow cue: faint stripes along seed direction
        float stripe = 0.5f + 0.5f * sin(12.0f * (x * v.x + y * v.y));
        color = lerp(color, color * 0.85f + float3(0.1f, 0.1f, 0.05f), stripe * 0.25f);
    }
    else
    {
        color = heat(saturate(gmag * 0.55f));
        // Flow ticks along ∇f
        float2 ghat = gmag > 1e-4f ? float2(dfdx, dfdy) / gmag : float2(1.0f, 0.0f);
        float flow = 0.5f + 0.5f * sin(10.0f * (x * ghat.x + y * ghat.y) - time);
        color = lerp(color, float3(1.0f, 0.95f, 0.5f), flow * 0.15f);
    }

    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

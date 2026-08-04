// SPDX-License-Identifier: Apache-2.0
// DiffSlang D03 — SIMT pixels vs tensor batches (mental model).
// Left: classic per-pixel shading (independent threads).
// Right: same math shown as a “batch grid” — ML-style layout over the same domain.
// Inspired by: https://developer.nvidia.com/blog/differentiable-slang-a-shading-language-for-renderers-that-learn/

module diffslang_d03_simt_vs_tensors;

import slangpy;

float3 shade(float2 uv, float time)
{
    float2 p = uv * 2.0f - 1.0f;
    float r = length(p);
    float ang = atan2(p.y, p.x);
    float lobes = 0.5f + 0.5f * cos(5.0f * ang + time);
    float ring = smoothstep(0.75f, 0.55f, r) * smoothstep(0.15f, 0.35f, r);
    float3 col = float3(0.15f + 0.7f * lobes, 0.25f + 0.4f * (1.0f - r), 0.55f + 0.35f * uv.x);
    return col * (0.35f + 0.65f * ring);
}

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 local = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);

    float3 color = shade(local, time);

    if (right)
    {
        // Overlay a soft batch lattice — reminds you tensors group many samples.
        float2 cell = frac(local * 8.0f);
        float grid = max(
            smoothstep(0.06f, 0.0f, min(cell.x, 1.0f - cell.x)),
            smoothstep(0.06f, 0.0f, min(cell.y, 1.0f - cell.y)));
        color = lerp(color, float3(0.95f, 0.92f, 0.55f), grid * 0.45f);
        // Corner badge: “batch”
        if (local.x > 0.72f && local.y < 0.12f)
            color = float3(0.2f, 0.55f, 0.85f);
    }
    else
    {
        // Corner badge: “pixel”
        if (local.x > 0.72f && local.y < 0.12f)
            color = float3(0.85f, 0.45f, 0.2f);
    }

    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

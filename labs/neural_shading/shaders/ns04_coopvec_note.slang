// SPDX-License-Identifier: Apache-2.0
// Neural shading NS04 — CoopVec / Tensor Core note (Phase 2 preview viz).
// Shows a matrix-vector “layer” as a heat diagram; real CoopVec is native Vulkan Phase 2.
// Inspired by: https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/

module neural_shading_ns04_coopvec_note;

import slangpy;

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    // Schematic: input vector (left bar) × weight matrix (grid) → output (right bar)
    float3 bg = float3(0.08f, 0.09f, 0.12f);
    float3 color = bg;

    // Weight matrix plate
    float2 m0 = float2(0.22f, 0.2f);
    float2 m1 = float2(0.72f, 0.8f);
    if (uv.x > m0.x && uv.x < m1.x && uv.y > m0.y && uv.y < m1.y)
    {
        float2 t = (uv - m0) / (m1 - m0);
        int cx = int(t.x * 8.0f);
        int cy = int(t.y * 6.0f);
        float cell = 0.35f + 0.25f * sin(float(cx) * 1.7f + float(cy) * 2.1f + time);
        float2 f = frac(float2(t.x * 8.0f, t.y * 6.0f));
        float border = max(smoothstep(0.08f, 0.0f, min(f.x, 1.0f - f.x)),
                           smoothstep(0.08f, 0.0f, min(f.y, 1.0f - f.y)));
        color = float3(0.15f + 0.5f * cell, 0.35f + 0.4f * cell, 0.75f);
        color = lerp(color, float3(0.05f, 0.06f, 0.08f), border * 0.7f);
    }

    // Input vector column
    if (uv.x > 0.06f && uv.x < 0.14f && uv.y > 0.25f && uv.y < 0.75f)
    {
        float ty = (uv.y - 0.25f) / 0.5f;
        color = float3(0.9f, 0.55f + 0.2f * sin(ty * 8.0f + time), 0.25f);
    }

    // Output vector column
    if (uv.x > 0.82f && uv.x < 0.9f && uv.y > 0.3f && uv.y < 0.7f)
    {
        float ty = (uv.y - 0.3f) / 0.4f;
        color = float3(0.3f, 0.85f, 0.55f + 0.2f * cos(ty * 6.0f - time));
    }

    // Pulse suggesting Tensor Core coop execution
    float pulse = 0.5f + 0.5f * sin(time * 3.0f);
    if (uv.y > 0.88f && uv.x > 0.2f && uv.x < 0.8f)
        color = lerp(float3(0.2f, 0.2f, 0.25f), float3(0.4f, 0.75f, 1.0f), pulse * step(uv.x, 0.2f + 0.6f * pulse));

    return color;
}

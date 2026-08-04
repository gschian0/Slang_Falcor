// SPDX-License-Identifier: Apache-2.0
// Neural GFX afternoon NG01 — “call Slang from Python” as a live hello.
// Same hello_pixel contract live uses; afternoon starts by deleting graphics boilerplate.
// Inspired by: https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/

module neural_gfx_ng01_slangpy_calls;

import slangpy;

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    // Soft “dispatch grid” — each pixel is one SlangPy call_id / grid cell.
    float2 cell = frac(uv * 12.0f);
    float grid = max(
        smoothstep(0.07f, 0.0f, min(cell.x, 1.0f - cell.x)),
        smoothstep(0.07f, 0.0f, min(cell.y, 1.0f - cell.y)));

    float pulse = 0.5f + 0.5f * sin(time * 2.0f + uv.x * 4.0f);
    float3 base = float3(0.12f + 0.5f * uv.x, 0.2f + 0.35f * uv.y, 0.55f + 0.3f * pulse);
    return lerp(base, float3(0.95f, 0.9f, 0.55f), grid * 0.55f);
}

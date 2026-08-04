// SPDX-License-Identifier: Apache-2.0
// Book of Shaders → Slang — 05 Patterns (tile / repeat)
// Inspired by The Book of Shaders (Patricio Gonzalez Vivo & Jen Lowe)
// https://thebookofshaders.com/09/

module bos_05_patterns;

import slangpy;

float sdCircle(float2 p, float r)
{
    return length(p) - r;
}

/// Tile UV space, draw a circle in each cell — classic repeat.
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    // Scale up then wrap to [0,1) per cell.
    float scale = 6.0f;
    float2 grid = uv * scale;
    float2 cell = floor(grid);
    float2 f = frac(grid);

    // Local centered coords in the cell.
    float2 p = f * 2.0f - 1.0f;

    // Slow radius wobble so tiles feel alive (uses live `time`).
    float r = 0.35f + 0.08f * sin(time * 1.7f + cell.x * 0.7f + cell.y * 1.1f);
    float d = sdCircle(p, r);
    float mask = 1.0f - smoothstep(-0.02f, 0.02f, d);

    // Checker-ish tint from cell index.
    float checker = fmod(cell.x + cell.y, 2.0f);
    float3 a = float3(0.15f, 0.55f, 0.90f);
    float3 b = float3(0.90f, 0.35f, 0.55f);
    float3 ink = lerp(a, b, checker);
    float3 bg = float3(0.06f, 0.07f, 0.09f);

    return lerp(bg, ink, mask);
}

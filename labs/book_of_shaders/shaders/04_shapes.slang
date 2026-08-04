// SPDX-License-Identifier: Apache-2.0
// Book of Shaders → Slang — 04 Shapes (SDF-style)
// Inspired by The Book of Shaders (Patricio Gonzalez Vivo & Jen Lowe)
// https://thebookofshaders.com/07/

module bos_04_shapes;

import slangpy;

float sdCircle(float2 p, float r)
{
    return length(p) - r;
}

float sdBox(float2 p, float2 b)
{
    float2 d = abs(p) - b;
    return length(max(d, float2(0.0f, 0.0f))) + min(max(d.x, d.y), 0.0f);
}

/// Soft edge from signed distance → [0,1] fill.
float fill(float d, float soft)
{
    return 1.0f - smoothstep(-soft, soft, d);
}

/// Circle + rounded-feeling rect on a dark field.
public float3 hello_pixel(int2 pixel, int2 resolution)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    // Centered coordinates, aspect-corrected.
    float2 p = uv * 2.0f - 1.0f;
    p.x *= float(resolution.x) / float(resolution.y);

    float circle = fill(sdCircle(p - float2(-0.35f, 0.1f), 0.35f), 0.01f);
    float box = fill(sdBox(p - float2(0.4f, -0.05f), float2(0.28f, 0.22f)), 0.012f);

    float3 bg = float3(0.08f, 0.09f, 0.12f);
    float3 cCol = float3(0.95f, 0.55f, 0.20f);
    float3 bCol = float3(0.25f, 0.75f, 0.85f);

    float3 color = bg;
    color = lerp(color, cCol, circle);
    color = lerp(color, bCol, box);
    return color;
}

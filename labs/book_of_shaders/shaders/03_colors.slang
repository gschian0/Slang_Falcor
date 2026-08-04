// SPDX-License-Identifier: Apache-2.0
// Book of Shaders → Slang — 03 Colors
// Inspired by The Book of Shaders (Patricio Gonzalez Vivo & Jen Lowe)
// https://thebookofshaders.com/06/

module bos_03_colors;

import slangpy;

/// Horizontal mix of two hues — Color panel drives ``color_a`` / ``color_b``.
public float3 hello_pixel(int2 pixel, int2 resolution, float3 color_a, float3 color_b)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    // Smoothstep the mix factor for a softer band than raw uv.x.
    float t = smoothstep(0.15f, 0.85f, uv.x);
    float3 color = lerp(color_a, color_b, t);

    // Gentle vertical vignette — still one idea: color mixing.
    float wash = 0.75f + 0.25f * uv.y;
    return color * wash;
}

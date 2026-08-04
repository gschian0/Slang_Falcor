// SPDX-License-Identifier: Apache-2.0
// Book of Shaders → Slang — 00 Hello
// Inspired by The Book of Shaders (Patricio Gonzalez Vivo & Jen Lowe)
// https://thebookofshaders.com/00/  https://thebookofshaders.com/01/

module bos_00_hello;

import slangpy;

/// Map a pixel to UV in [0,1]^2 and return a simple color.
public float3 hello_pixel(int2 pixel, int2 resolution)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    // Try: solid color → return float3(0.15f, 0.55f, 0.95f);
    // Try: flip axes, boost green, etc.
    return float3(uv.x, uv.y, 0.35f);
}

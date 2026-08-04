// SPDX-License-Identifier: Apache-2.0
// Book of Shaders → Slang — 02 Shaping functions
// Inspired by The Book of Shaders (Patricio Gonzalez Vivo & Jen Lowe)
// https://thebookofshaders.com/05/

module bos_02_shaping;

import slangpy;

/// Soft line around y = f(x) for curve-plotting in UV space.
float plot(float2 st, float pct)
{
    return smoothstep(pct - 0.02f, pct, st.y) -
           smoothstep(pct, pct + 0.02f, st.y);
}

/// Plot y = pow(x, 3) (or swap in smoothstep / sin). Green line on gray field.
public float3 hello_pixel(int2 pixel, int2 resolution)
{
    float2 st = (float2(pixel) + 0.5f) / float2(resolution);

    // Flip Y so the curve rises like a graph (origin bottom-left).
    st.y = 1.0f - st.y;

    float y = pow(st.x, 3.0f);
    // Alternatives to try:
    // float y = smoothstep(0.1f, 0.9f, st.x);
    // float y = 0.5f + 0.5f * sin(st.x * 6.2831853f);

    float3 color = float3(y, y, y);
    float pct = plot(st, y);
    color = (1.0f - pct) * color + pct * float3(0.15f, 0.95f, 0.35f);
    return color;
}

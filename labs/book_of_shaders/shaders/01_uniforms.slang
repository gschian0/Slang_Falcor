// SPDX-License-Identifier: Apache-2.0
// Book of Shaders → Slang — 01 Uniforms (time)
// Inspired by The Book of Shaders (Patricio Gonzalez Vivo & Jen Lowe)
// https://thebookofshaders.com/03/
//
// Live passes `time` as seconds since the preview started.

module bos_01_uniforms;

import slangpy;

/// Soft pulse: brightness breathes with sin(time).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    // 0.5 + 0.5*sin → [0,1] oscillator
    float pulse = 0.5f + 0.5f * sin(time * 2.0f);

    // Base tint from UV; multiply by pulse so the whole frame breathes.
    float3 base = float3(uv.x, 0.35f + 0.4f * uv.y, 0.85f - 0.3f * uv.x);
    return base * (0.35f + 0.65f * pulse);
}

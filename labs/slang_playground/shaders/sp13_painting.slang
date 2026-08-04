// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Painting" demo (procedural brush stand-in).
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/painting.slang
// Playground: https://shader-slang.org/slang-playground/
// Original: mouse + persistent RWTexture + indirect dispatch. Live has no sticky
// canvas — animate a soft brush along a path so the educational brush falloff shows.
// © shader-slang — adapted.

module sp13_painting;

import slangpy;

float brush(float2 uv, float2 center, float brush_size)
{
    float2 offset = (uv - center) * float2(1.0f, 1.0f);
    // Match playground: length(offset) > brush_size/2 in pixel space ≈ soft disk in UV.
    float r = brush_size * 0.5f;
    return 1.0f - smoothstep(r * 0.85f, r, length(offset));
}

/// Magenta brush orbiting (playground COLOR_PICK default was magenta).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float3 canvas = float3(1.0f, 1.0f, 1.0f); // BLACK_SCREEN inverted → white paper feel
    // Actually playground BLACK_SCREEN starts black; use dark canvas.
    canvas = float3(0.05f, 0.05f, 0.06f);

    float3 color_pick = float3(1.0f, 0.0f, 1.0f);
    float brush_size = 0.12f; // ~slider mid in UV units

    // Trail of recent brush stamps along a Lissajous path.
    float3 color = canvas;
    for (int i = 0; i < 24; i++)
    {
        float t = time - float(i) * 0.05f;
        float2 center = float2(0.5f + 0.35f * sin(t * 1.1f), 0.5f + 0.3f * sin(t * 1.7f));
        float m = brush(uv, center, brush_size) * (1.0f - float(i) / 28.0f);
        color = lerp(color, color_pick, m);
    }
    return color;
}

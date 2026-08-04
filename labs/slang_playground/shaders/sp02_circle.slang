// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "ShaderToy: Circle" demo.
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/circle.slang
// Playground: https://shader-slang.org/slang-playground/
// Based on https://www.shadertoy.com/view/XdlSDs by dynamite (CC BY-NC-SA 3.0).
// © shader-slang / ShaderToy author — adapted drawPixel → hello_pixel.
// 3x3 supersample softens beam edges vs the official playground look.

module sp02_circle;

import slangpy;

static const int AA = 3;

float3 render_circle(float2 frag, float2 screen, float time)
{
    float2 p = (frag * 2.0f - screen) / screen.y;
    float tau = 6.28318530718f;
    float a = atan2(p.x, p.y);
    float r = length(p) * 0.75f;
    float2 uv = float2(a / tau, r);
    float t = time;

    float xCol = (uv.x - t / 3.0f) * 3.0f;
    xCol = fmod(abs(xCol), 3.0f);
    float3 horColour = float3(0.25f, 0.25f, 0.25f);

    if (xCol < 1.0f)
    {
        horColour.r += 1.0f - xCol;
        horColour.g += xCol;
    }
    else if (xCol < 2.0f)
    {
        xCol -= 1.0f;
        horColour.g += 1.0f - xCol;
        horColour.b += xCol;
    }
    else
    {
        xCol -= 2.0f;
        horColour.b += 1.0f - xCol;
        horColour.r += xCol;
    }

    uv = (2.0f * uv) - 1.0f;
    float lobes = clamp(floor(5.0f + 10.0f * cos(t)), 0.0f, 10.0f);
    float beamWidth =
        (0.7f + 0.5f * cos(uv.x * 10.0f * tau * 0.15f * lobes))
        * abs(1.0f / (30.0f * uv.y));
    return horColour * beamWidth;
}

/// Polar color beams spinning with time (ShaderToy circle look).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 screen = float2(resolution);
    // ShaderToy-style: Y+ up vs our top-left pixel origin.
    float2 base = float2(float(pixel.x), float(resolution.y - 1 - pixel.y));
    float3 acc = float3(0.0f, 0.0f, 0.0f);
    for (int j = 0; j < AA; j++)
    {
        for (int i = 0; i < AA; i++)
        {
            float2 off = float2(
                (float(i) + 0.5f) / float(AA),
                (float(j) + 0.5f) / float(AA));
            float2 frag = base + float2(off.x, 1.0f - off.y);
            acc += render_circle(frag, screen, time);
        }
    }
    return acc / float(AA * AA);
}

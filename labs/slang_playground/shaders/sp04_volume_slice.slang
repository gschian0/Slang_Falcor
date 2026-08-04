// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Volume Slice" demo.
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/volume-slice.slang
// Playground: https://shader-slang.org/slang-playground/
// Original fills RWTexture3D once then slices; here the density field is evaluated
// analytically per pixel (same wave formula).
// © shader-slang — adapted.

module sp04_volume_slice;

import slangpy;

float volume_density(float3 uvw)
{
    float wave = sin(uvw.x * 6.2831853f) * cos(uvw.y * 6.2831853f) * sin(uvw.z * 6.2831853f);
    return 0.5f * (wave + 1.0f);
}

/// Animated Z-slice through a procedural 3D density field.
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float slice = frac(time * 0.2f);
    float value = volume_density(float3(uv.x, uv.y, slice));
    return float3(value, value * 0.6f, 1.0f - value);
}

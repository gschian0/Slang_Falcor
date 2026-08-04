// SPDX-License-Identifier: Apache-2.0
// Simple Image — sample a Texture2D (cowboy hat photo) with UV from pixel/resolution.
// Live binds image + samp from curriculum texture; optional float3 tint via Color panel.
// © Slang_Falcon / VERNACULAR — educational hello_pixel texture path.

module sp16_simple_image;

import slangpy;

/// Sample the bound photo; tint multiplies RGB (default white = identity).
public float3 hello_pixel(
    int2 pixel,
    int2 resolution,
    Texture2D image,
    SamplerState samp,
    float3 tint)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    // Flip V so PNG row 0 (top) maps to UV y=1 in typical D3D-style SampleLevel.
    float2 uv_flip = float2(uv.x, 1.0f - uv.y);
    float4 c = image.SampleLevel(samp, uv_flip, 0);
    return c.rgb * tint;
}

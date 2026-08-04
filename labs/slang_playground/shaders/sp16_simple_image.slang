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
    // pixel (0,0) is top-left — matches PIL row 0 / SampleLevel UV y=0.
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float4 c = image.SampleLevel(samp, uv, 0);
    return c.rgb * tint;
}

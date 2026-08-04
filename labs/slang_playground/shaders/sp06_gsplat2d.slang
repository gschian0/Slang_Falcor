// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "2D Splatter" demo (educational subset).
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/gsplat2d.slang
// Playground: https://shader-slang.org/slang-playground/
// Original uses groupshared coarse/fine raster + random buffer; here a fixed set of
// symmetric Gaussians is alpha-composited per pixel.
// © shader-slang — adapted.

module sp06_gsplat2d;

import slangpy;

float hash11(float n)
{
    return frac(sin(n) * 43758.5453123f);
}

float2 hash21(float n)
{
    return float2(hash11(n), hash11(n + 19.19f));
}

float3 hash31(float n)
{
    return float3(hash11(n), hash11(n + 7.7f), hash11(n + 13.13f));
}

float4 eval_gauss(float2 uv, float2 center, float sigma, float3 color)
{
    float2 diff = uv - center;
    float dist = dot(diff, diff);
    float weight = exp(-dist / (2.0f * sigma * sigma));
    return float4(color, weight);
}

float4 alpha_blend(float4 pixel, float4 gval)
{
    float4 p = float4(gval.rgb * gval.a, gval.a);
    return float4(pixel.rgb + p.rgb * pixel.a, pixel.a * (1.0f - p.a));
}

/// Front-to-back soft blobs — playground 2D Gaussian splatter look.
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float4 color = float4(0.0f, 0.0f, 0.0f, 1.0f);

    const int N = 48;
    for (int i = 0; i < N; i++)
    {
        float id = float(i) + 1.0f;
        float2 center = hash21(id * 12.9898f);
        center += 0.02f * float2(sin(time * 0.7f + id), cos(time * 0.5f + id * 1.3f));
        float sigma = 0.02f + 0.04f * hash11(id * 3.1f);
        float3 col = 0.35f + 0.65f * hash31(id * 5.5f);
        float4 gval = eval_gauss(uv, center, sigma, col);
        color = alpha_blend(color, gval);
        if (color.a < 0.01f)
            break;
    }

    float3 bg = float3(0.06f, 0.07f, 0.09f);
    return color.rgb * (1.0f - color.a) + bg * color.a;
}

// SPDX-License-Identifier: Apache-2.0
// Neural GFX afternoon NG02 — why gradients: target vs random blobs + loss heat.
// Left: target. Middle: current blobs. Right: per-pixel L2 heat.
// Inspired by: https://shader-slang.org/blog/2025/04/04/neural-gfx-in-an-afternoon/

module neural_gfx_ng02_why_gradients;

import slangpy;

float3 target_img(float2 uv)
{
    float2 p = uv * 2.0f - 1.0f;
    float d = length(p - float2(-0.15f, 0.1f));
    float blob = exp(-d * d * 14.0f);
    float d2 = length(p - float2(0.35f, -0.2f));
    float blob2 = exp(-d2 * d2 * 10.0f);
    return float3(0.9f * blob + 0.2f * blob2, 0.35f * blob + 0.7f * blob2, 0.2f + 0.5f * blob);
}

float3 gaussian(float2 uv, float2 center, float sigma, float3 col)
{
    float2 d = (uv - center) / max(sigma, 1e-3f);
    float w = exp(-dot(d, d));
    return col * w;
}

float3 render_blobs(float2 uv, float time)
{
    // “Untrained” random-ish blobs that slowly drift (pre-optimization chaos).
    float3 c = float3(0.05f, 0.05f, 0.07f);
    c += gaussian(uv, float2(0.3f + 0.05f * sin(time), 0.4f), 0.18f, float3(0.9f, 0.3f, 0.2f));
    c += gaussian(uv, float2(0.7f, 0.55f + 0.04f * cos(time * 0.8f)), 0.22f, float3(0.2f, 0.6f, 0.9f));
    c += gaussian(uv, float2(0.5f + 0.08f * sin(time * 1.3f), 0.7f), 0.15f, float3(0.9f, 0.85f, 0.3f));
    return saturate(c);
}

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float strip = uv.x * 3.0f;
    int panel = int(min(strip, 2.999f));
    float2 local = float2(frac(strip), uv.y);

    float3 tgt = target_img(local);
    float3 pred = render_blobs(local, time);
    float3 color;
    if (panel == 0)
        color = tgt;
    else if (panel == 1)
        color = pred;
    else
    {
        float3 e = pred - tgt;
        float L = dot(e, e);
        color = float3(L * 4.0f, L * 1.5f, 0.1f + L * 0.5f);
    }

    float xpix = float(pixel.x);
    float w = float(resolution.x);
    if (abs(xpix - w / 3.0f) < 1.5f || abs(xpix - 2.0f * w / 3.0f) < 1.5f)
        color = float3(0.9f, 0.9f, 0.85f);
    return color;
}

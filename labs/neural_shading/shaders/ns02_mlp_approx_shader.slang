// SPDX-License-Identifier: Apache-2.0
// Neural shading NS02 — MLP approximates a shader (teacher | MLP | abs-diff).
// Ties to neural/n02 and python -m slang_falcon.train_brdf.
// Inspired by: https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/

module neural_shading_ns02_mlp_approx_shader;

import slangpy;

static const float PI = 3.14159265358979323846f;

float3 teacher(float2 uv, float time)
{
    float ndotl = saturate(uv.x);
    float rough = saturate(0.15f + 0.7f * uv.y);
    float wobble = 0.05f * sin(time * 1.2f);
    float3 albedo = float3(0.2f, 0.55f, 0.85f);
    float a = max((rough + wobble) * (rough + wobble), 1e-4f);
    float NdotH = ndotl;
    float t = 1.0f + (a * a - 1.0f) * NdotH * NdotH;
    float D = (a * a) / (PI * t * t);
    return (albedo / PI) * ndotl + float3(D * 0.05f * ndotl);
}

float3 mlp_approx(float2 uv)
{
    float x0 = saturate(uv.x);
    float x1 = saturate(uv.y);
    float h[8];
    float w0_0[8] = { 1.6f, -1.1f, 2.0f, 0.5f, -1.4f, 0.9f, 1.2f, -0.4f };
    float w0_1[8] = { -0.8f, 1.7f, 0.4f, -1.5f, 1.1f, -0.5f, 2.1f, 0.7f };
    float b0[8] = { 0.05f, -0.3f, 0.15f, 0.4f, -0.1f, 0.0f, -0.5f, 0.25f };
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
        h[i] = max(w0_0[i] * x0 + w0_1[i] * x1 + b0[i], 0.0f);

    float3 o = float3(0.02f, 0.04f, 0.06f);
    float wr[8] = { 0.22f, -0.1f, 0.18f, 0.08f, -0.12f, 0.1f, 0.25f, -0.05f };
    float wg[8] = { 0.12f, 0.2f, -0.08f, 0.15f, 0.1f, -0.06f, 0.18f, 0.09f };
    float wb[8] = { 0.28f, 0.05f, 0.22f, -0.1f, 0.14f, 0.12f, 0.2f, 0.07f };
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
    {
        o.x += wr[i] * h[i];
        o.y += wg[i] * h[i];
        o.z += wb[i] * h[i];
    }
    return saturate(o);
}

/// Three strips: teacher | MLP | 4*|diff|
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float strip = uv.x * 3.0f;
    int panel = int(min(strip, 2.999f));
    float2 local = float2(frac(strip), uv.y);

    float3 t = teacher(local, time);
    float3 m = mlp_approx(local);
    float3 color;
    if (panel == 0)
        color = t;
    else if (panel == 1)
        color = m;
    else
        color = saturate(4.0f * abs(t - m));

    float xpix = float(pixel.x);
    float w = float(resolution.x);
    if (abs(xpix - w / 3.0f) < 1.5f || abs(xpix - 2.0f * w / 3.0f) < 1.5f)
        color = float3(0.9f, 0.9f, 0.85f);
    return color;
}

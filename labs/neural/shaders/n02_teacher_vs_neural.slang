// SPDX-License-Identifier: Apache-2.0
// Neural curriculum N02 — analytic teacher | tiny MLP | abs-diff strip.
// Compact Disney-ish lobe for live demo; baked 2→8→3 MLP (ndotl, roughness → RGB).
// Full train path: python -m slang_falcon.train_brdf → assets/weights/brdf_mlp.bin

module neural_n02_teacher_vs_neural;

import slangpy;

static const float PI = 3.14159265358979323846f;

float3 teacher_brdf(float ndotl, float roughness)
{
    float3 albedo = float3(0.8f, 0.15f, 0.1f);
    float NdotL = saturate(ndotl);
    float a = max(roughness * roughness, 1e-4f);
    // Fake N·H ≈ N·L for a fixed view (teaching slice, not full BRDF).
    float NdotH = NdotL;
    float t = 1.0f + (a * a - 1.0f) * NdotH * NdotH;
    float D = (a * a) / (PI * t * t);
    float3 diff = (albedo / PI) * NdotL;
    float3 spec = float3(D * 0.04f * NdotL);
    return diff + spec;
}

float3 mlp_brdf(float ndotl, float roughness)
{
    float x0 = saturate(ndotl);
    float x1 = saturate(roughness);

    float h[8];
    // Demo weights: rough match to teacher_brdf on a coarse grid (not SFMLP001).
    float w0_0[8] = { 1.8f, -0.9f, 2.2f, 0.4f, -1.5f, 1.1f, 0.7f, -0.3f };
    float w0_1[8] = { -1.2f, 2.0f, 0.5f, -1.8f, 1.4f, -0.6f, 2.4f, 0.9f };
    float b0[8] = { 0.1f, -0.4f, 0.2f, 0.5f, -0.2f, 0.0f, -0.6f, 0.3f };
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
        h[i] = max(w0_0[i] * x0 + w0_1[i] * x1 + b0[i], 0.0f);

    float3 outc = float3(0.02f, 0.01f, 0.01f);
    float wr[8] = { 0.22f, 0.05f, 0.18f, 0.08f, 0.12f, 0.15f, 0.10f, 0.06f };
    float wg[8] = { 0.04f, 0.10f, 0.03f, 0.07f, 0.05f, 0.02f, 0.08f, 0.04f };
    float wb[8] = { 0.03f, 0.08f, 0.02f, 0.06f, 0.04f, 0.01f, 0.07f, 0.03f };
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
    {
        outc.x += wr[i] * h[i];
        outc.y += wg[i] * h[i];
        outc.z += wb[i] * h[i];
    }
    return max(outc, float3(0.0f));
}

float3 tonemap(float3 c)
{
    return c / (c + 1.0f);
}

/// Three panels: teacher | neural | 4×|diff|.
public float3 hello_pixel(int2 pixel, int2 resolution)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float panel = floor(uv.x * 3.0f);
    float u = frac(uv.x * 3.0f);
    float ndotl = u;
    float rough = 0.05f + 0.9f * uv.y;

    float3 t = teacher_brdf(ndotl, rough);
    float3 n = mlp_brdf(ndotl, rough);
    float3 d = abs(t - n) * 4.0f;

    float3 c = panel < 0.5f ? t : (panel < 1.5f ? n : d);
    c = tonemap(c);

    // Panel seams
    float seam = min(abs(uv.x - 1.0f / 3.0f), abs(uv.x - 2.0f / 3.0f));
    if (seam < 1.2f / float(resolution.x))
        c = float3(0.85f, 0.85f, 0.8f);
    return c;
}

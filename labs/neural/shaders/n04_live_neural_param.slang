// SPDX-License-Identifier: Apache-2.0
// Neural curriculum N04 — BoS uniforms meet neural shading.
// float time (live) + editable u_gain drive a tiny 3→8→3 color net.

module neural_n04_live_neural_param;

import slangpy;

/// Edit this like a BoS uniform — live debounce recompiles.
static const float u_gain = 1.0f;

float3 tiny_net(float2 uv, float t, float gain)
{
    float x0 = uv.x;
    float x1 = uv.y;
    float x2 = 0.5f + 0.5f * sin(t * 1.7f + gain);

    float h[8];
    float w0a[8] = { 1.2f, -0.8f, 0.9f, 1.5f, -1.1f, 0.4f, 0.7f, -0.5f };
    float w0b[8] = { 0.6f, 1.4f, -0.9f, 0.3f, 1.0f, -1.2f, 0.5f, 0.8f };
    float w0c[8] = { 0.9f, -0.4f, 1.3f, -0.7f, 0.2f, 1.1f, -0.6f, 0.5f };
    float b0[8] = { -0.2f, 0.3f, -0.1f, 0.4f, 0.0f, -0.3f, 0.2f, 0.1f };
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
        h[i] = max(w0a[i] * x0 + w0b[i] * x1 + w0c[i] * x2 + b0[i], 0.0f);

    float3 c = float3(0.05f, 0.04f, 0.08f);
    float wr[8] = { 0.20f, 0.05f, 0.15f, 0.10f, 0.08f, 0.12f, 0.06f, 0.09f };
    float wg[8] = { 0.08f, 0.18f, 0.06f, 0.14f, 0.11f, 0.04f, 0.16f, 0.07f };
    float wb[8] = { 0.12f, 0.07f, 0.20f, 0.05f, 0.15f, 0.10f, 0.04f, 0.13f };
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
    {
        c.x += wr[i] * h[i];
        c.y += wg[i] * h[i];
        c.z += wb[i] * h[i];
    }
    // Gain scales the network’s “exposure” — uniform → neural look.
    return saturate(c * gain);
}

/// UV + time + u_gain → neural-ish shading.
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float gain = u_gain * (0.75f + 0.35f * (0.5f + 0.5f * sin(time * 0.4f)));
    return tiny_net(uv, time, gain);
}

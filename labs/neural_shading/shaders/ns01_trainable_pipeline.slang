// SPDX-License-Identifier: Apache-2.0
// Neural shading NS01 — trainable pipeline intuition.
// Left: fixed analytical shade. Right: same shade with editable/trainable-looking params (gain, bias)
// that breathe with time — stand-in for GradOutTensor parameters in a real train loop.
// Inspired by: https://developer.nvidia.com/blog/how-to-get-started-with-neural-shading-for-your-game-or-application/

module neural_shading_ns01_trainable_pipeline;

import slangpy;

float3 analytic(float2 uv, float gain, float bias)
{
    float2 p = uv * 2.0f - 1.0f;
    float ndotl = saturate(0.55f + 0.45f * p.x);
    float rough = saturate(0.2f + 0.6f * uv.y);
    float3 albedo = float3(0.75f, 0.35f, 0.2f);
    float3 col = albedo * ndotl * (0.4f + 0.6f * (1.0f - rough));
    return saturate(col * gain + bias);
}

/// Left: frozen “authored” shade. Right: params drift (proxy for optimization).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 local = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);

    float gain_fixed = 1.0f;
    float bias_fixed = 0.0f;
    // Trainable-looking knobs: wander as if an optimizer were updating them.
    float gain_train = 0.75f + 0.45f * sin(time * 0.55f);
    float bias_train = 0.08f * sin(time * 0.9f + 1.2f);

    float3 color = right
        ? analytic(local, gain_train, bias_train)
        : analytic(local, gain_fixed, bias_fixed);

    // Param readout bars at bottom of right panel
    if (right && local.y > 0.9f)
    {
        float gx = local.x;
        float gbar = step(gx, saturate((gain_train - 0.3f) / 1.2f));
        color = lerp(float3(0.12f, 0.12f, 0.14f), float3(0.3f, 0.85f, 0.55f), gbar);
    }

    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

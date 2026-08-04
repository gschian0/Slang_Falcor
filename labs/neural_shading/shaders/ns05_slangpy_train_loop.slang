// SPDX-License-Identifier: Apache-2.0
// Neural shading NS05 — SlangPy train-loop stages as a live schematic.
// Stages light up with time: forward → loss → bwd_diff → Adam → repeat.
// Companion doc walks the real train_brdf / afternoon Python loop.

module neural_shading_ns05_slangpy_train_loop;

import slangpy;

public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float3 bg = float3(0.07f, 0.08f, 0.1f);
    float3 color = bg;

    // Four boxes along x
    float phase = fmod(time * 0.55f, 4.0f);
    int cur = int(phase);

    float2 boxes[4];
    boxes[0] = float2(0.05f, 0.22f);
    boxes[1] = float2(0.28f, 0.45f);
    boxes[2] = float2(0.51f, 0.68f);
    boxes[3] = float2(0.74f, 0.91f);

    float3 cols[4];
    cols[0] = float3(0.35f, 0.75f, 0.95f); // forward
    cols[1] = float3(0.95f, 0.55f, 0.3f);  // loss
    cols[2] = float3(0.9f, 0.35f, 0.7f);   // bwd
    cols[3] = float3(0.4f, 0.9f, 0.55f);   // adam

    [ForceUnroll]
    for (int i = 0; i < 4; ++i)
    {
        float x0 = boxes[i].x;
        float x1 = boxes[i].y;
        if (uv.x > x0 && uv.x < x1 && uv.y > 0.35f && uv.y < 0.65f)
        {
            float active = (i == cur) ? 1.0f : 0.35f;
            color = cols[i] * active;
            // Inner hatch
            float hatch = 0.5f + 0.5f * sin((uv.x + uv.y) * 40.0f);
            color = lerp(color, color * 0.85f, hatch * 0.2f);
        }
        // Arrows between boxes
        if (i < 3)
        {
            float ax0 = x1;
            float ax1 = boxes[i + 1].x;
            if (uv.y > 0.48f && uv.y < 0.52f && uv.x > ax0 && uv.x < ax1)
                color = float3(0.75f, 0.75f, 0.7f);
        }
    }

    // Loop-back arc at bottom
    if (uv.y > 0.78f && uv.y < 0.82f && uv.x > 0.1f && uv.x < 0.9f)
        color = float3(0.45f, 0.45f, 0.5f);
    if (uv.x > 0.08f && uv.x < 0.12f && uv.y > 0.5f && uv.y < 0.8f)
        color = float3(0.45f, 0.45f, 0.5f);
    if (uv.x > 0.88f && uv.x < 0.92f && uv.y > 0.5f && uv.y < 0.8f)
        color = float3(0.45f, 0.45f, 0.5f);

    return color;
}

// SPDX-License-Identifier: Apache-2.0
// Feedback F0 stub — simulates video feedback trails without ping-pong RTs.
// Plan: docs/plans/vsynth-feedback.md
// Live today: single hello_pixel → RGB (no previous-frame texture). True ping-pong
// needs a small host extension (two buffers + sample prev). Until then, stamp a
// soft ink blob along a warped path and decay older stamps like feedback amount.

module fb01_pingpong;

import slangpy;

float2 rot(float2 p, float a)
{
    float c = cos(a);
    float s = sin(a);
    return float2(c * p.x - s * p.y, s * p.x + c * p.y);
}

/// Soft disk in UV space (ink for the "new frame" layer).
float blob(float2 uv, float2 center, float radius)
{
    return 1.0f - smoothstep(radius * 0.55f, radius, length(uv - center));
}

/// Simulated ping-pong feedback: trail of transformed stamps + decay.
/// Uniforms-as-constants stand in for a future feedback/zoom/spin panel.
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float2 p = uv - 0.5f;

    // Artist knobs (edit + hot-reload). Map to live uniforms in real F0.
    float feedback = 0.92f; // persistence / decay of older stamps
    float zoom = 1.015f;    // >1 pulls trail inward each "generation"
    float spin = 0.04f;     // radians per stamp step

    float3 canvas = float3(0.02f, 0.02f, 0.03f);
    float3 ink = float3(0.95f, 0.35f, 0.2f);
    float3 accent = float3(0.2f, 0.75f, 0.95f);

    float3 color = canvas;
    const int taps = 48;
    for (int i = 0; i < taps; i++)
    {
        float fi = float(i);
        float t = time - fi * 0.04f;
        // Fresh ink wanders; older samples pretend to be previous RTs after zoom+spin.
        float2 center = float2(0.12f * sin(t * 1.3f), 0.1f * cos(t * 1.7f));
        float2 q = p;
        for (int k = 0; k < i; k++)
        {
            q = rot(q, spin) * zoom;
        }
        float2 sample_uv = q + 0.5f + center * pow(feedback, fi * 0.15f);
        float m = blob(sample_uv, float2(0.5f, 0.5f), 0.08f);
        float age = pow(feedback, fi);
        float3 tint = lerp(ink, accent, frac(fi * 0.07f + time * 0.05f));
        color = lerp(color, tint, m * age);
    }

    // Mild vignette so the recursive zoom reads as a tunnel.
    float vig = smoothstep(0.95f, 0.25f, length(p));
    return color * vig;
}

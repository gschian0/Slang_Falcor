// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Image From URL" demo (procedural stand-in).
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/image-from-url.slang
// Playground: https://shader-slang.org/slang-playground/
// Original samples Texture2D loaded from URL (jeep.jpg). Live hello_pixel has no
// URL binder — sample a procedural "photo": cool shades smiley (cyber vibe).
// Local fallback asset: assets/images/cool_shades_smiley.png
// © shader-slang — adapted.

module sp14_image_from_url;

import slangpy;

float sd_circle(float2 p, float r)
{
    return length(p) - r;
}

float sd_box(float2 p, float2 b)
{
    float2 d = abs(p) - b;
    return length(max(d, 0.0f)) + min(max(d.x, d.y), 0.0f);
}

float sd_rounded_box(float2 p, float2 b, float r)
{
    return sd_box(p, b - r) - r;
}

/// Cool funny smiley in shades — cyber/shader playground vibe (URL stand-in).
float3 cool_shades_smiley(float2 uv)
{
    // Center + slight letterbox crop space
    float2 p = (uv - 0.5f) * float2(1.15f, 1.15f);

    // Neon grid backdrop
    float2 g = abs(frac(p * 8.0f) - 0.5f);
    float grid = smoothstep(0.04f, 0.0f, min(g.x, g.y));
    float3 bg = float3(0.04f, 0.06f, 0.12f);
    bg += float3(0.0f, 0.45f, 0.55f) * grid * 0.35f;
    float glow = exp(-8.0f * length(p));
    bg += float3(0.15f, 0.05f, 0.35f) * glow;

    // Face
    float face = sd_circle(p, 0.38f);
    float3 face_col = float3(1.0f, 0.86f, 0.18f);
    // Soft cheek blush
    float blush_l = exp(-80.0f * length(p - float2(-0.18f, -0.08f)));
    float blush_r = exp(-80.0f * length(p - float2(0.18f, -0.08f)));
    face_col = lerp(face_col, float3(1.0f, 0.45f, 0.35f), (blush_l + blush_r) * 0.35f);

    float3 col = lerp(face_col, bg, smoothstep(-0.01f, 0.012f, face));

    // Cool shades (two lenses + bridge + arms)
    float2 left_c = float2(-0.14f, 0.08f);
    float2 right_c = float2(0.14f, 0.08f);
    float lens_l = sd_rounded_box(p - left_c, float2(0.13f, 0.09f), 0.04f);
    float lens_r = sd_rounded_box(p - right_c, float2(0.13f, 0.09f), 0.04f);
    float bridge = sd_rounded_box(p - float2(0.0f, 0.08f), float2(0.04f, 0.025f), 0.01f);
    float arm_l = sd_rounded_box(p - float2(-0.30f, 0.08f), float2(0.06f, 0.018f), 0.008f);
    float arm_r = sd_rounded_box(p - float2(0.30f, 0.08f), float2(0.06f, 0.018f), 0.008f);
    float shades = min(min(lens_l, lens_r), min(bridge, min(arm_l, arm_r)));

    // Reflective cyber lenses
    float3 lens_base = float3(0.05f, 0.08f, 0.12f);
    float2 lp = p - left_c;
    float2 rp = p - right_c;
    float3 cyan = float3(0.2f, 0.95f, 1.0f);
    float3 mag = float3(1.0f, 0.2f, 0.85f);
    float3 lens_col = lens_base;
    if (lens_l < 0.0f)
        lens_col = lerp(lens_base, cyan, 0.55f + 0.35f * lp.x + 0.2f * lp.y);
    if (lens_r < 0.0f)
        lens_col = lerp(lens_base, mag, 0.55f - 0.35f * rp.x + 0.2f * rp.y);
    // Frame rim
    float3 frame = float3(0.08f, 0.08f, 0.1f);
    float in_shades = smoothstep(0.008f, -0.004f, shades);
    float rim = smoothstep(0.012f, 0.0f, abs(shades));
    col = lerp(col, frame, rim * 0.9f);
    col = lerp(col, lens_col, in_shades);

    // Smile (arc)
    float2 sm = p - float2(0.0f, -0.06f);
    float smile_ring = abs(length(sm) - 0.18f) - 0.018f;
    float smile_mask = step(sm.y, -0.02f);
    float smile = smoothstep(0.01f, -0.005f, smile_ring) * smile_mask;
    col = lerp(col, float3(0.15f, 0.08f, 0.05f), smile);

    // Scanline / CRT touch
    float scan = 0.92f + 0.08f * sin(uv.y * 420.0f);
    col *= scan;

    // Photo vignette
    float v = smoothstep(0.95f, 0.35f, length(uv - 0.5f));
    return col * v;
}

/// Aspect-correct UV sample with Y flip (playground SampleLevel path).
public float3 hello_pixel(int2 pixel, int2 resolution)
{
    float2 scaled = float2(pixel) / float(resolution.y);
    float2 flipped = float2(scaled.x, 1.0f - scaled.y);
    // Letterbox when wider than tall
    if (flipped.x < 0.0f || flipped.x > float(resolution.x) / float(resolution.y))
        return float3(0.06f, 0.07f, 0.1f);
    float2 uv = float2(flipped.x * float(resolution.y) / float(resolution.x), flipped.y);
    return cool_shades_smiley(uv);
}

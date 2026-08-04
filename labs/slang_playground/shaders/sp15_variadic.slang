// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Variadic Generics" demo → image.
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/variadic.slang
// Playground: https://shader-slang.org/slang-playground/
// Educational intent: IMyPrintable-style interface + multi-arg "print all" → color bands.
// © shader-slang — adapted.

module sp15_variadic;

import slangpy;

interface IMyTintable
{
    float3 tint();
}

extension float : IMyTintable
{
    float3 tint()
    {
        float t = saturate(this / 10.0f);
        return float3(t, 0.4f, 1.0f - t);
    }
}

extension int : IMyTintable
{
    float3 tint()
    {
        float t = saturate(float(this) / 5.0f);
        return float3(0.2f, t, 0.55f);
    }
}

// Playground: printAllWithTypePrefix<T>(expand each T args) where T : IMyPrintable
float3 tint_one<T : IMyTintable>(T v)
{
    return v.tint();
}

/// Color bands from mixed int/float args (variadic print demo → image).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    int a = 1 + int(2.0f + 2.0f * sin(time));
    int b = 2;
    float c = 3.0f + sin(time);
    float d = 4.0f;

    // Same call-site idea as printAllWithTypePrefix(1, 2, 3.0, 4.0)
    float3 t0 = tint_one(a);
    float3 t1 = tint_one(b);
    float3 t2 = tint_one(c);
    float3 t3 = tint_one(d);
    float3 mixed = (t0 + t1 + t2 + t3) * 0.25f;

    int band = clamp(int(uv.x * 4.0f), 0, 3);
    float3 bandCol = band == 0 ? t0 : (band == 1 ? t1 : (band == 2 ? t2 : t3));
    bool bottom = uv.y < 0.25f;
    return bottom ? mixed : bandCol * (0.55f + 0.45f * uv.y);
}

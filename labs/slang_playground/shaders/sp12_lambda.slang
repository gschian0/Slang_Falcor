// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Lambda Expressions" demo → image.
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/lambda.slang
// Playground: https://shader-slang.org/slang-playground/
// © shader-slang — adapted.

module sp12_lambda;

import slangpy;

public struct MyData
{
    public int data[4];

    MyData map(IFunc<int, int> f)
    {
        MyData result;
        for (int i = 0; i < 4; i++)
            result.data[i] = f(data[i]);
        return result;
    }
}

float bar(float2 uv, float x0, float x1, float h)
{
    if (uv.x < x0 || uv.x > x1)
        return 0.0f;
    return 1.0f - smoothstep(h, h + 0.02f, uv.y);
}

/// Bars: input {1,2,3,4} vs lambda map x → 2x+env (playground print demo).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    MyData p;
    p.data[0] = 1;
    p.data[1] = 2;
    p.data[2] = 3;
    p.data[3] = 4;

    int env = 1 + int(2.0f + 2.0f * sin(time));
    let q = p.map((int x) => x * 2 + env);

    float3 bg = float3(0.08f, 0.09f, 0.11f);
    float3 color = bg;

    for (int i = 0; i < 4; i++)
    {
        float x0 = 0.08f + float(i) * 0.22f;
        float x1 = x0 + 0.08f;
        float hin = float(p.data[i]) / 12.0f;
        float hout = float(q.data[i]) / 20.0f;
        color = lerp(color, float3(0.35f, 0.55f, 0.85f), bar(uv, x0, x1, hin));
        color = lerp(color, float3(0.9f, 0.55f, 0.25f), bar(uv, x0 + 0.09f, x1 + 0.09f, hout));
    }
    return color;
}

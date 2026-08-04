// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Generics & Extensions" demo → image.
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/generic.slang
// Playground: https://shader-slang.org/slang-playground/
// © shader-slang — adapted.

module sp10_generics;

import slangpy;

interface IMyHashable
{
    int getHash();
}

struct Circle : IMyHashable
{
    float2 position;
    float radius;

    __init(float2 p, float r)
    {
        position = p;
        radius = r;
    }

    int getHash()
    {
        return bit_cast<int>(position.x) ^ bit_cast<int>(position.y) ^ bit_cast<int>(radius);
    }
}

extension float : IMyHashable
{
    int getHash()
    {
        return bit_cast<int>(this);
    }
}

extension<T : IMyHashable, int N> vector<T, N> : IMyHashable
{
    int getHash()
    {
        int hash = 0;
        for (int i = 0; i < N; i++)
            hash ^= this[i].getHash();
        return hash;
    }
}

float3 hash_color(int h)
{
    float u = frac(float(h) * 0.000001f + 0.5f);
    float v = frac(float(h >> 8) * 0.0000013f);
    float w = frac(float(h >> 16) * 0.0000009f);
    return float3(0.25f + 0.75f * u, 0.25f + 0.75f * v, 0.25f + 0.75f * w);
}

int printHash<T : IMyHashable>(T obj)
{
    return obj.getHash();
}

/// Left: Circle hash color · right: float3 hash via extensions.
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;

    float2 pos = float2(1.0f + 0.2f * sin(time), 2.0f + 0.2f * cos(time));
    Circle circle = Circle(pos, 3.0f + 0.5f * sin(time * 0.5f));
    float3 v = float3(1.0f, 2.0f + 0.3f * sin(time), 3.0f);

    float3 left = hash_color(printHash(circle));
    float3 rightCol = hash_color(printHash(v));

    // Soft disk showing the Circle lives in the left panel.
    float2 lp = float2(uv.x * 2.0f, uv.y);
    float d = length(lp - float2(0.5f, 0.5f)) - 0.25f;
    float disk = 1.0f - smoothstep(0.0f, 0.02f, d);

    float3 color = right ? rightCol : lerp(left * 0.35f, left, disk);
    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.88f, 0.88f, 0.82f);
    return color;
}

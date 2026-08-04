// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Properties" demo → image.
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/property.slang
// Playground: https://shader-slang.org/slang-playground/
// © shader-slang — adapted.

module sp09_properties;

import slangpy;

public struct MyPoint
{
    private uint data;

    public property float x
    {
        get { return (data & 0xFFFFu) / 65535.0f; }
        set { data = (data & 0xFFFF0000u) | (uint)(newValue * 65535.0f); }
    }

    public property float y
    {
        get { return (data >> 16) / 65535.0f; }
        set { data = (data & 0xFFFFu) | ((uint)(newValue * 65535.0f) << 16); }
    }
}

/// Draw packed property points as soft markers (playground printed P=(0.5,0.25)).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    MyPoint p;
    p.x = 0.5f + 0.2f * sin(time);
    p.y = 0.25f + 0.15f * cos(time * 0.8f);

    MyPoint q;
    q.x = 0.3f;
    q.y = 0.7f;

    float3 bg = float3(0.08f, 0.09f, 0.12f);
    float d0 = length(uv - float2(p.x, p.y));
    float d1 = length(uv - float2(q.x, q.y));
    float m0 = 1.0f - smoothstep(0.02f, 0.05f, d0);
    float m1 = 1.0f - smoothstep(0.02f, 0.05f, d1);

    float3 color = bg;
    color = lerp(color, float3(0.95f, 0.55f, 0.25f), m0);
    color = lerp(color, float3(0.3f, 0.75f, 0.9f), m1);
    return color;
}

// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Operator Overload" demo → image.
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/operator-overload.slang
// Playground: https://shader-slang.org/slang-playground/
// © shader-slang — adapted.

module sp11_operator_overload;

import slangpy;

struct MyPoint
{
    float x;
    float y;
    __init(float _x, float _y)
    {
        this.x = _x;
        this.y = _y;
    }

    __subscript(int i) -> float
    {
        get
        {
            if (i == 0)
                return x;
            if (i == 1)
                return y;
            return 0.0f;
        }
        set
        {
            if (i == 0)
                x = newValue;
            if (i == 1)
                y = newValue;
        }
    }
}

MyPoint operator+(MyPoint a, MyPoint b)
{
    return MyPoint(a.x + b.x, a.y + b.y);
}

float marker(float2 uv, float2 p)
{
    return 1.0f - smoothstep(0.015f, 0.04f, length(uv - p));
}

/// Visualize p0, p1, and overloaded p0+p1 (then subscript write on y).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);

    // Scale playground numbers (1,2)+(3,4) into UV space.
    MyPoint p0 = MyPoint(0.2f + 0.05f * sin(time), 0.3f);
    MyPoint p1 = MyPoint(0.35f, 0.25f + 0.05f * cos(time));
    var p2 = p0 + p1;
    // Playground then does p2[1] = 10; we nudge y with subscript to show it works.
    p2[1] = saturate(p2[1] * 0.55f + 0.05f * sin(time * 1.3f));

    float3 bg = float3(0.07f, 0.08f, 0.1f);
    float3 color = bg;
    color = lerp(color, float3(0.95f, 0.4f, 0.3f), marker(uv, float2(p0[0], p0[1])));
    color = lerp(color, float3(0.35f, 0.7f, 0.95f), marker(uv, float2(p1[0], p1[1])));
    color = lerp(color, float3(0.9f, 0.85f, 0.3f), marker(uv, float2(p2[0], p2[1])));

    // Segment p0→p2
    float2 a = float2(p0[0], p0[1]);
    float2 b = float2(p2[0], p2[1]);
    float2 ab = b - a;
    float t = saturate(dot(uv - a, ab) / max(dot(ab, ab), 1e-5f));
    float line = 1.0f - smoothstep(0.004f, 0.012f, length(uv - (a + ab * t)));
    color = lerp(color, float3(0.5f, 0.5f, 0.45f), line * 0.5f);
    return color;
}

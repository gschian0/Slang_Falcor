// SPDX-License-Identifier: Apache-2.0
// Neural curriculum N03 — autodiff intuition in pixels.
// Loss landscape L(x,y) = (f(x,y) - target)^2 with analytic grad magnitude overlay.
// Teaching viz only — real Slang autodiff uses [Differentiable] + .bwds (Lab 2 / Lab 4).

module neural_n03_autodiff_intuition;

import slangpy;

/// Teacher scalar field (smooth “bowl + saddle” mix).
[Differentiable]
float field(float x, float y)
{
    // x,y in [-1,1]
    return 0.55f * (x * x + 0.7f * y * y) + 0.25f * sin(3.0f * x) * cos(2.0f * y);
}

[Differentiable]
float loss(float x, float y, float target)
{
    float e = field(x, y) - target;
    return e * e;
}

/// Manual gradient of loss (matches what autodiff would emit for this tiny fn).
void loss_grad(float x, float y, float target, out float gx, out float gy)
{
    float f = field(x, y);
    float e = f - target;
    // dfield/dx, dfield/dy
    float dfdx = 0.55f * 2.0f * x + 0.25f * 3.0f * cos(3.0f * x) * cos(2.0f * y);
    float dfdy = 0.55f * 2.0f * 0.7f * y - 0.25f * sin(3.0f * x) * 2.0f * sin(2.0f * y);
    // d(e^2)/dvar = 2 e * df/dvar
    gx = 2.0f * e * dfdx;
    gy = 2.0f * e * dfdy;
}

float3 heatmap(float t)
{
    t = saturate(t);
    return float3(t, 0.2f + 0.5f * t, 1.0f - t);
}

/// Left: loss landscape. Right: |∇L| (where autodiff pushes parameters).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    bool right = uv.x >= 0.5f;
    float2 p = float2(right ? (uv.x - 0.5f) * 2.0f : uv.x * 2.0f, uv.y);
    // Map to [-1,1]^2
    float x = p.x * 2.0f - 1.0f;
    float y = (1.0f - p.y) * 2.0f - 1.0f;

    float target = 0.35f + 0.15f * sin(time * 0.7f);
    float L = loss(x, y, target);
    float gx, gy;
    loss_grad(x, y, target, gx, gy);
    float gmag = sqrt(gx * gx + gy * gy);

    float3 color;
    if (!right)
        color = heatmap(L * 2.5f);
    else
        color = heatmap(saturate(gmag * 1.2f));

    // Moving optimum marker (where L is near 0 for current target — approximate)
    // Show a soft ring at a reference point that crawls with time.
    float2 mark = float2(0.35f * sin(time * 0.5f), 0.25f * cos(time * 0.4f));
    float d = length(float2(x, y) - mark);
    float ring = smoothstep(0.08f, 0.05f, d) - smoothstep(0.05f, 0.02f, d);
    color = lerp(color, float3(1.0f, 0.95f, 0.4f), ring * 0.85f);

    if (abs(uv.x - 0.5f) < 1.5f / float(resolution.x))
        color = float3(0.9f, 0.9f, 0.85f);
    return color;
}

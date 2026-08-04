// SPDX-License-Identifier: Apache-2.0
// Minimal compute kernels for Lab 1 / Lab 2 teaching examples.

module lab_kernels;

import slangpy;

/// Lab 1: write a UV gradient into an image buffer.
public float3 hello_pixel(int2 pixel, int2 resolution)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    return float3(sin(15.0*uv.x), uv.y, 0.25f);
}

/// Lab 2: tiny differentiable function f(x) = (ax^2 + bx + c)^2
/// Prefer calling `.bwds(...)` from Python (SlangPy Tensor path) rather than
/// hand-writing `bwd_diff` here — see labs/02_autodiff.md.
[Differentiable]
public float polynomial(float a, float b, float c, float x)
{
    float y = a * x * x + b * x + c;
    return y * y;
}

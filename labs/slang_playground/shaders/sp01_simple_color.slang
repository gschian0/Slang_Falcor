// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Simple Image" demo — renamed Simple Color (it returns a solid color).
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/simple-image.slang
// Playground: https://shader-slang.org/slang-playground/
// © shader-slang — adapted from WebGPU drawPixel → hello_pixel.

module sp01_simple_color;

import slangpy;

/// Solid flat color — live Color panel drives ``float3 color``.
public float3 hello_pixel(int2 pixel, int2 resolution, float3 color)
{
    // Original playground: drawPixel(..., (_) => float4(0.3, 0.7, 0.55, 1.0))
    return color;
}

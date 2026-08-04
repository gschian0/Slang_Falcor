// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "Multi-kernel Demo".
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/multiple-kernels.slang
// Playground: https://shader-slang.org/slang-playground/
// Original: fillBuffer kernel writes a sine table, imageMain samples it.
// Live path has one entry — same sine wave evaluated inline (multi-pass story in .md).
// © shader-slang — adapted.

module sp05_multi_kernel;

import slangpy;

float fill_sample(uint idx, float time)
{
    return sin(float(idx) / 1000.0f + 10.0f * time);
}

/// Visualize a "buffer" of sine values as grayscale (one-kernel stand-in).
public float3 hello_pixel(int2 pixel, int2 resolution, float time)
{
    uint idx = uint(pixel.x + pixel.y * resolution.x);
    float v = fill_sample(idx % 131072u, time);
    float g = 0.5f + 0.5f * v;
    return float3(g, g, g);
}

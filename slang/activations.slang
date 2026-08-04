// SPDX-License-Identifier: Apache-2.0
// Shared activations (teaching / native reuse).
// Phase 1 SlangPy train path inlines these inside train_brdf.slang for reliable loading.

module activations;

[Differentiable]
public float relu(float x)
{
    return max(x, 0.0f);
}

[Differentiable]
public float leaky_relu(float x, float slope)
{
    return x >= 0.0f ? x : slope * x;
}

[Differentiable]
public float sigmoid(float x)
{
    return 1.0f / (1.0f + exp(-x));
}

[Differentiable]
public float softplus(float x)
{
    return log(1.0f + exp(x));
}

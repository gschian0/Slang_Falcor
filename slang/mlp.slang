// SPDX-License-Identifier: Apache-2.0
// Tiny differentiable MLP used for BRDF / texture approximation.
// Architecture: INPUTS -> HIDDEN -> HIDDEN -> OUTPUTS with ReLU (linear output optional).

module mlp;

import slangpy;

[Differentiable]
float relu(float x)
{
    return max(x, 0.0f);
}

[Differentiable]
float softplus(float x)
{
    return log(1.0f + exp(x));
}

/// One fully-connected layer with atomic gradient accumulation for batched training.
public struct LinearLayer<let Inputs : int, let Outputs : int>
{
    Tensor<float, 1> biases;
    Tensor<float, 2> weights;

    AtomicTensor<float, 1> biases_grad;
    AtomicTensor<float, 2> weights_grad;

    [Differentiable]
    float get_bias(int neuron)
    {
        return biases.load(neuron);
    }

    [Differentiable]
    float get_weight(int neuron, int input)
    {
        return weights.load(neuron, input);
    }

    [BackwardDerivativeOf(get_bias)]
    void get_bias_bwd(int neuron, float grad)
    {
        biases_grad.add(neuron, grad);
    }

    [BackwardDerivativeOf(get_weight)]
    void get_weight_bwd(int neuron, int input, float grad)
    {
        weights_grad.add(neuron, input, grad);
    }

    [Differentiable]
    float[Outputs] forward(float[Inputs] x)
    {
        float[Outputs] y;
        [MaxIters(Outputs)]
        for (int row = 0; row < Outputs; ++row)
        {
            var sum = get_bias(row);
            [ForceUnroll]
            for (int col = 0; col < Inputs; ++col)
                sum += get_weight(row, col) * x[col];
            y[row] = sum;
        }
        return y;
    }
}

/// Default BRDF MLP: 5 features -> 32 -> 32 -> 3 (RGB).
public struct BrdfMLP
{
    LinearLayer<5, 32> layer0;
    LinearLayer<32, 32> layer1;
    LinearLayer<32, 3> layer2;

    [Differentiable]
    float3 eval(float features[5])
    {
        float h0[32] = layer0.forward(features);
        [ForceUnroll]
        for (int i = 0; i < 32; ++i)
            h0[i] = relu(h0[i]);

        float h1[32] = layer1.forward(h0);
        [ForceUnroll]
        for (int i = 0; i < 32; ++i)
            h1[i] = relu(h1[i]);

        float out[3] = layer2.forward(h1);
        [ForceUnroll]
        for (int i = 0; i < 3; ++i)
            out[i] = softplus(out[i]);
        return float3(out[0], out[1], out[2]);
    }
}

/// Adam step for a single parameter (vectorized over tensors from Python).
public void optimizer_step(
    inout float primal,
    inout float grad,
    inout float mean,
    inout float variance,
    float learning_rate,
    int iteration)
{
    const float ADAM_BETA_1 = 0.9f;
    const float ADAM_BETA_2 = 0.999f;
    const float ADAM_EPSILON = 1e-8f;

    mean = lerp(grad, mean, ADAM_BETA_1);
    variance = lerp(grad * grad, variance, ADAM_BETA_2);

    float mHat = mean / (1.0f - pow(ADAM_BETA_1, float(iteration)));
    float vHat = variance / (1.0f - pow(ADAM_BETA_2, float(iteration)));
    float step = learning_rate * mHat / (sqrt(vHat) + ADAM_EPSILON);

    primal -= step;
    grad = 0.0f;
}

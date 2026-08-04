// SPDX-License-Identifier: Apache-2.0
// Self-contained BRDF MLP train/infer kernels for SlangPy (Phase 1).
// Kept in one translation unit so module visibility stays simple.

import slangpy;

// ---- activations ----

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

// ---- Disney teacher (compact) ----

static const float PI = 3.14159265358979323846f;

[Differentiable]
float schlick(float u)
{
    float m = saturate(1.0f - u);
    float m2 = m * m;
    return m2 * m2 * m;
}

[Differentiable]
float gtr2(float NdotH, float a)
{
    float a2 = a * a;
    float t = 1.0f + (a2 - 1.0f) * NdotH * NdotH;
    return a2 / (PI * t * t);
}

[Differentiable]
float smith_ggx(float NdotV, float alphaG)
{
    float a = alphaG * alphaG;
    float b = NdotV * NdotV;
    return 1.0f / (NdotV + sqrt(a + b - a * b));
}

[Differentiable]
float3 eval_disney_brdf(
    float3 albedo,
    float3 L,
    float3 V,
    float3 N,
    float roughness,
    float metallic,
    float specular)
{
    float NdotL = dot(N, L);
    float NdotV = dot(N, V);
    if (NdotL < 0.0f || NdotV < 0.0f)
        return float3(0.0f);

    float3 H = normalize(L + V);
    float NdotH = dot(N, H);
    float LdotH = dot(L, H);

    float3 Cspec0 = lerp(specular * float3(0.08f), albedo, metallic);
    float FL = schlick(NdotL);
    float FV = schlick(NdotV);
    float Fd90 = 0.5f + 2.0f * LdotH * LdotH * roughness;
    float Fd = lerp(1.0f, Fd90, FL) * lerp(1.0f, Fd90, FV);

    float a = max(roughness * roughness, 1e-4f);
    float Ds = gtr2(NdotH, a);
    float FH = schlick(LdotH);
    float3 Fs = lerp(Cspec0, float3(1.0f), FH);
    float Gs = smith_ggx(NdotL, a) * smith_ggx(NdotV, a);

    float3 color = ((1.0f / PI) * Fd * albedo) * (1.0f - metallic) + Gs * Fs * Ds;
    return color * max(0.0f, NdotL);
}

void pack_brdf_features(float3 L, float3 V, float3 N, float roughness, out float features[5])
{
    float3 H = normalize(L + V);
    features[0] = saturate(dot(N, L));
    features[1] = saturate(dot(N, V));
    features[2] = saturate(dot(N, H));
    features[3] = saturate(dot(L, H));
    features[4] = saturate(roughness);
}

// ---- MLP ----

struct LinearLayer<let Inputs : int, let Outputs : int>
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

struct BrdfMLP
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

void optimizer_step(
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

// ---- train / render ----

struct LCG
{
    uint state;

    __init(uint seed)
    {
        state = seed;
    }

    [mutating]
    uint next_uint()
    {
        state = 1664525u * state + 1013904223u;
        return state;
    }

    [mutating]
    float next_float()
    {
        return (next_uint() >> 8) * 0x1p-24;
    }
};

float3 sample_hemisphere(inout LCG rng)
{
    float u1 = rng.next_float();
    float u2 = rng.next_float();
    float r = sqrt(u1);
    float phi = 6.28318530718f * u2;
    return float3(r * cos(phi), r * sin(phi), sqrt(max(0.0f, 1.0f - u1)));
}

static const float3 kAlbedo = float3(0.8f, 0.15f, 0.1f);
static const float kMetallic = 0.0f;
static const float kSpecular = 0.5f;
static const float3 kNormal = float3(0.0f, 0.0f, 1.0f);

[Differentiable]
float3 sample_loss(no_diff float features[5], no_diff float3 teacher, BrdfMLP network)
{
    float3 pred = network.eval(features);
    float3 err = pred - teacher;
    return err * err;
}

void train_sample(uint seed, BrdfMLP network)
{
    LCG rng = LCG(seed);
    float3 L = sample_hemisphere(rng);
    float3 V = sample_hemisphere(rng);
    float roughness = 0.05f + 0.9f * rng.next_float();

    float features[5];
    pack_brdf_features(L, V, kNormal, roughness, features);

    float3 teacher = eval_disney_brdf(kAlbedo, L, V, kNormal, roughness, kMetallic, kSpecular);
    bwd_diff(sample_loss)(features, teacher, network, float3(1.0f, 1.0f, 1.0f));
}

float3 loss_sample(uint seed, BrdfMLP network)
{
    LCG rng = LCG(seed);
    float3 L = sample_hemisphere(rng);
    float3 V = sample_hemisphere(rng);
    float roughness = 0.05f + 0.9f * rng.next_float();

    float features[5];
    pack_brdf_features(L, V, kNormal, roughness, features);

    float3 teacher = eval_disney_brdf(kAlbedo, L, V, kNormal, roughness, kMetallic, kSpecular);
    return sample_loss(features, teacher, network);
}

float3 render_slice(int2 pixel, int2 resolution, BrdfMLP network, int mode)
{
    float2 uv = (float2(pixel) + 0.5f) / float2(resolution);
    float ndotl = uv.x;
    float roughness = 0.05f + 0.9f * uv.y;

    float3 L = normalize(float3(sqrt(max(0.0f, 1.0f - ndotl * ndotl)), 0.0f, ndotl));
    float3 V = normalize(float3(0.2f, 0.3f, 0.9f));

    float features[5];
    pack_brdf_features(L, V, kNormal, roughness, features);

    float3 teacher = eval_disney_brdf(kAlbedo, L, V, kNormal, roughness, kMetallic, kSpecular);
    float3 pred = network.eval(features);

    float3 color;
    if (mode == 0)
        color = teacher;
    else if (mode == 1)
        color = pred;
    else
        color = abs(teacher - pred) * 4.0f;

    return color / (color + 1.0f);
}

float3 infer_features(float features[5], BrdfMLP network)
{
    return network.eval(features);
}

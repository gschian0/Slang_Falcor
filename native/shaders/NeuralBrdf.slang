// SPDX-License-Identifier: Apache-2.0
// Falcor / Vulkan neural BRDF inference (scalar path + CoopVec hooks).
// Matches Phase 1 feature packing and SFMLP001 layer order.

module NeuralBrdf;

#ifndef SF_USE_COOPVEC
#define SF_USE_COOPVEC 0
#endif

static const float PI = 3.14159265358979323846f;

float relu(float x) { return max(x, 0.0f); }
float softplus(float x) { return log(1.0f + exp(x)); }

float3 disneyTeacher(float3 albedo, float3 L, float3 V, float3 N, float roughness)
{
    // Compact mirror of slang/disney_brdf.slang for viewport toggle.
    float NdotL = saturate(dot(N, L));
    float NdotV = saturate(dot(N, V));
    if (NdotL <= 0.0f || NdotV <= 0.0f) return float3(0.0f);
    float3 H = normalize(L + V);
    float NdotH = saturate(dot(N, H));
    float LdotH = saturate(dot(L, H));
    float a = max(roughness * roughness, 1e-4);
    float a2 = a * a;
    float t = 1.0f + (a2 - 1.0f) * NdotH * NdotH;
    float D = a2 / (PI * t * t);
    float3 diff = (albedo / PI) * NdotL;
    float3 spec = float3(D) * 0.04f * NdotL;
    return diff + spec;
}

void packFeatures(float3 L, float3 V, float3 N, float roughness, out float f[5])
{
    float3 H = normalize(L + V);
    f[0] = saturate(dot(N, L));
    f[1] = saturate(dot(N, V));
    f[2] = saturate(dot(N, H));
    f[3] = saturate(dot(L, H));
    f[4] = saturate(roughness);
}

/// Scalar MLP forward (debug / non-CoopVec). Weights in row-major flat buffer.
float3 mlpForwardScalar(float features[5], ByteAddressBuffer weights, uint bias0, uint weight0)
{
    // Layer sizes 5→32→32→3. Offsets computed by host to match SFMLP001 flatten order.
    // This stub reads sequentially: host binds a structured layout matching WeightLoader::flatten.
    float h0[32];
    uint cursor = 0;
    // Host should pack: b0[32], W0[32*5], b1[32], W1[32*32], b2[3], W2[3*32]
    // For readability the production pass uses RTXNS InferenceMLP when SF_USE_COOPVEC.
    float x[5] = features;
    // Minimal portable eval expects Python-exported layout uploaded as float buffer.
    // Full index math lives in the Falcor C++ binder; here we expose the entry signature.
    return float3(x[0], x[4], 0.2f); // placeholder tint until buffer binders land
}

#if SF_USE_COOPVEC
// Hook: replace with rtxns::mlp::InferenceMLP / CoopVec path (see RTXNS docs).
float3 mlpForwardCoopVec(float features[5], ByteAddressBuffer weights)
{
    return mlpForwardScalar(features, weights, 0, 0);
}
#endif

struct NeuralBrdfConstants
{
    int mode; // 0 teacher, 1 neural, 2 diff
    float pad0;
    float2 pad1;
};

float3 evalPixel(float2 uv, NeuralBrdfConstants cb, ByteAddressBuffer mlpWeights)
{
    float ndotl = uv.x;
    float roughness = 0.05f + 0.9f * uv.y;
    float3 N = float3(0, 0, 1);
    float3 L = normalize(float3(sqrt(max(0.0f, 1.0f - ndotl * ndotl)), 0.0f, ndotl));
    float3 V = normalize(float3(0.2f, 0.3f, 0.9f));
    float3 albedo = float3(0.8f, 0.15f, 0.1f);

    float features[5];
    packFeatures(L, V, N, roughness, features);

    float3 teacher = disneyTeacher(albedo, L, V, N, roughness);
#if SF_USE_COOPVEC
    float3 neural = mlpForwardCoopVec(features, mlpWeights);
#else
    float3 neural = mlpForwardScalar(features, mlpWeights, 0, 0);
#endif

    if (cb.mode == 0) return teacher;
    if (cb.mode == 2) return abs(teacher - neural) * 4.0f;
    return neural;
}

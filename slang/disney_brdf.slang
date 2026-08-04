// SPDX-License-Identifier: Apache-2.0
// Disney principled BRDF teacher (analytic). Differentiable for loss / diagnostics.

module disney_brdf;

static const float PI = 3.14159265358979323846f;

[Differentiable]
float clamp01(float x)
{
    return max(min(x, 1.0f), 0.0f);
}

[Differentiable]
float sqr(float x)
{
    return x * x;
}

[Differentiable]
float SchlickFresnel(float u)
{
    float m = clamp01(1.0f - u);
    float m2 = m * m;
    return m2 * m2 * m;
}

[Differentiable]
float GTR2(float NdotH, float a)
{
    float a2 = a * a;
    float t = 1.0f + (a2 - 1.0f) * NdotH * NdotH;
    return a2 / (PI * t * t);
}

[Differentiable]
float smithG_GGX(float NdotV, float alphaG)
{
    float a = alphaG * alphaG;
    float b = NdotV * NdotV;
    return 1.0f / (NdotV + sqrt(a + b - a * b));
}

/// Core Disney BRDF (no N·L cosine term).
[Differentiable]
public float3 DisneyBRDF(
    float3 baseColor,
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

    float3 Cdlin = baseColor;
    float Cdlum = 0.3f * Cdlin.x + 0.6f * Cdlin.y + 0.1f * Cdlin.z;
    float3 Ctint = Cdlum > 0.0f ? Cdlin / Cdlum : float3(1.0f);
    float3 Cspec0 = lerp(specular * float3(0.08f), Cdlin, metallic);

    float FL = SchlickFresnel(NdotL);
    float FV = SchlickFresnel(NdotV);
    float Fd90 = 0.5f + 2.0f * LdotH * LdotH * roughness;
    float Fd = lerp(1.0f, Fd90, FL) * lerp(1.0f, Fd90, FV);

    float a = max(sqr(roughness), 1e-4f);
    float Ds = GTR2(NdotH, a);
    float FH = SchlickFresnel(LdotH);
    float3 Fs = lerp(Cspec0, float3(1.0f), FH);
    float Gs = smithG_GGX(NdotL, a) * smithG_GGX(NdotV, a);

    return ((1.0f / PI) * Fd * Cdlin) * (1.0f - metallic) + Gs * Fs * Ds;
}

/// Teacher eval with cosine term (outgoing radiance factor for a directional light).
[Differentiable]
public float3 eval_disney_brdf(
    float3 albedo,
    float3 light_dir,
    float3 view_dir,
    float3 normal,
    float roughness,
    float metallic,
    float specular)
{
    float3 brdf = DisneyBRDF(albedo, light_dir, view_dir, normal, roughness, metallic, specular);
    return brdf * max(0.0f, dot(normal, light_dir));
}

/// Pack the five scalar features used by the BRDF MLP (matches RTXNS-style encoding).
public void pack_brdf_features(
    float3 L,
    float3 V,
    float3 N,
    float roughness,
    out float features[5])
{
    float3 H = normalize(L + V);
    features[0] = saturate(dot(N, L));
    features[1] = saturate(dot(N, V));
    features[2] = saturate(dot(N, H));
    features[3] = saturate(dot(L, H));
    features[4] = saturate(roughness);
}

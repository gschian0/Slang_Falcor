// VERNACULAR shading ladder — classic properties → physical (Disney-ish analytic).
// Included by VernacularViewport.3d.slang. Expects hash helpers + PerFrameCB + getSunDirection().

float3 shadeLambert(float3 N, float3 albedo)
{
    float3 L = getSunDirection();
    float ndotl = saturate(dot(N, L));
    return albedo * ndotl + albedo * 0.08f;
}

float3 shadeBlinn(float3 N, float3 V, float3 albedo)
{
    float3 L = getSunDirection();
    float3 H = normalize(L + V);
    float ndotl = saturate(dot(N, L));
    float ndoth = saturate(dot(N, H));
    return albedo * ndotl + float3(0.9f, 0.9f, 0.95f) * pow(ndoth, 64.f) * ndotl + albedo * 0.06f;
}

// Full / physical — GGX + Schlick F + Smith G; maps classics into one BRDF.
float3 shadePhysical(float3 N, float3 V, float3 baseColor, float roughness, float metallic)
{
    float3 L = getSunDirection();
    float3 H = normalize(L + V);
    float NdotL = saturate(dot(N, L));
    float NdotV = max(1e-4f, saturate(dot(N, V)));
    float NdotH = saturate(dot(N, H));
    float VdotH = saturate(dot(V, H));

    float3 F0 = lerp(float3(0.04f, 0.04f, 0.04f), baseColor, metallic);
    float3 F = F0 + (1.f - F0) * pow(1.f - VdotH, 5.f);

    float a = max(0.001f, roughness * roughness);
    float a2 = a * a;
    float d = NdotH * NdotH * (a2 - 1.f) + 1.f;
    float D = a2 / (3.14159265f * d * d);

    float k = (roughness + 1.f) * (roughness + 1.f) / 8.f;
    float Gv = NdotV / (NdotV * (1.f - k) + k);
    float Gl = NdotL / (NdotL * (1.f - k) + k);
    float G = Gv * Gl;

    float3 spec = (D * G * F) / max(1e-4f, 4.f * NdotV * NdotL);
    float3 kd = (1.f - F) * (1.f - metallic);
    float3 diffuse = kd * baseColor / 3.14159265f;

    // Scale like a bright key so Physical reads richer than Blinn on same cubes
    return (diffuse + spec) * NdotL * 3.5f + baseColor * 0.05f;
}

float3 chapterSplatter(float2 uv, float t)
{
    float3 color = float3(0.05f, 0.06f, 0.08f);
    for (int i = 0; i < 36; i++)
    {
        float id = float(i) + 1.f;
        float2 center = hash21(id * 12.9898f);
        center += 0.03f * float2(sin(t * 0.7f + id), cos(t * 0.5f + id * 1.3f));
        float sigma = 0.03f + 0.05f * hash11(id * 3.1f);
        float3 col = 0.35f + 0.65f * hash31(id * 5.5f);
        float2 d = uv - center;
        float a = exp(-dot(d, d) / (2.f * sigma * sigma));
        color = lerp(color, col, saturate(a));
    }
    return color;
}

float3 chapterPaint(float2 uv, float t)
{
    float3 color = float3(0.06f, 0.05f, 0.07f);
    for (int i = 0; i < 20; i++)
    {
        float tt = t - float(i) * 0.06f;
        float2 center = float2(0.5f + 0.35f * sin(tt * 1.1f), 0.5f + 0.3f * sin(tt * 1.7f));
        float brush = 1.f - smoothstep(0.08f, 0.12f, length(uv - center));
        float3 ink = float3(1.f, 0.15f + 0.2f * sin(tt), 0.85f);
        color = lerp(color, ink, brush * (1.f - float(i) / 24.f));
    }
    return color;
}

float3 chapterPotluck(float2 uv, float3 N, float t)
{
    float3 a = hash31(floor(uv.x * 8.f) + floor(uv.y * 8.f) * 17.f + floor(t));
    float3 b = hash31(floor(uv.x * 8.f + 3.f) + floor(uv.y * 8.f) * 9.f);
    float wob = 0.5f + 0.5f * sin(t * 2.f + uv.x * 10.f);
    return shadeLambert(N, lerp(a, b, wob));
}

float3 chapterNeural(float2 uv, float t)
{
    float x0 = uv.x;
    float x1 = uv.y;
    float x2 = 0.5f + 0.5f * sin(t * 1.7f);
    float h[8];
    float w0a[8] = {1.2f, -0.8f, 0.9f, 1.5f, -1.1f, 0.4f, 0.7f, -0.5f};
    float w0b[8] = {0.6f, 1.4f, -0.9f, 0.3f, 1.0f, -1.2f, 0.5f, 0.8f};
    float w0c[8] = {0.9f, -0.4f, 1.3f, -0.7f, 0.2f, 1.1f, -0.6f, 0.5f};
    float b0[8] = {-0.2f, 0.3f, -0.1f, 0.4f, 0.0f, -0.3f, 0.2f, 0.1f};
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
        h[i] = max(w0a[i] * x0 + w0b[i] * x1 + w0c[i] * x2 + b0[i], 0.0f);
    float3 c = float3(0.05f, 0.04f, 0.08f);
    float wr[8] = {0.20f, 0.05f, 0.15f, 0.10f, 0.08f, 0.12f, 0.06f, 0.09f};
    float wg[8] = {0.08f, 0.18f, 0.06f, 0.14f, 0.11f, 0.04f, 0.16f, 0.07f};
    float wb[8] = {0.12f, 0.07f, 0.20f, 0.05f, 0.15f, 0.10f, 0.04f, 0.13f};
    [ForceUnroll]
    for (int i = 0; i < 8; ++i)
    {
        c.x += wr[i] * h[i];
        c.y += wg[i] * h[i];
        c.z += wb[i] * h[i];
    }
    return saturate(c * (0.9f + 0.3f * sin(t * 0.4f)));
}

float3 chapterModeViz(float3 posW, float3 N, float t)
{
    int2 mode;
    float w = vibrationMode(posW, t, mode);
    float3 base = float3(0.15f, 0.2f, 0.35f);
    float3 hot = float3(1.f, 0.45f, 0.1f);
    float3 cold = float3(0.2f, 0.7f, 1.f);
    float3 field = lerp(cold, hot, saturate(w * 0.5f + 0.5f));
    return shadeLambert(N, lerp(base, field, 0.85f));
}

float3 shadeChapterLook(float2 uv, float3 N, float3 V, float3 posW, float3 albedo)
{
    if (gChapter == 0)
        return float3(uv, 0.f);
    if (gChapter == 1)
        return N * 0.5f + 0.5f;
    if (gChapter == 2)
        return shadeLambert(N, albedo);
    if (gChapter == 3)
        return shadeBlinn(N, V, albedo);
    if (gChapter == 4)
    {
        // Space monkey — roughness/metal vary slightly by face so Physical ≠ flat Blinn
        float rough = 0.28f + 0.35f * hash11(floor(uv.x * 4.f) + floor(uv.y * 4.f) * 7.f);
        float metal = 0.05f + 0.55f * saturate(uv.x * 0.6f + 0.2f);
        return shadePhysical(N, V, albedo, rough, metal);
    }
    if (gChapter == 5)
        return chapterSplatter(uv, gTime);
    if (gChapter == 6)
        return chapterPaint(uv, gTime);
    if (gChapter == 7)
        return chapterPotluck(uv, N, gTime);
    if (gChapter == 8)
        return chapterNeural(uv, gTime);
    if (gChapter == 9)
        return chapterModeViz(posW, N, gTime);
    if (gChapter == 10)
        return shadeLambert(N, chapterSplatter(uv, gTime));
    if (gChapter == 11)
        return shadeBlinn(N, V, chapterNeural(uv, gTime));
    if (gChapter == 12)
        return chapterPotluck(uv, N, gTime) + 0.15f * chapterPaint(uv, gTime * 0.7f);

    // School ports (Iteration 3 temple bank) — BoS / playground spirit on canvas
    if (gChapter == 13)
    {
        // sp02 circle — radial beam / lobe ring
        float2 p = uv * 2.f - 1.f;
        float r = length(p);
        float a = atan2(p.y, p.x);
        float t = gTime;
        float ring = smoothstep(0.08f, 0.02f, abs(r - (0.55f + 0.08f * sin(t * 2.f))));
        float spokes = 0.5f + 0.5f * sin(a * 6.f + t);
        float3 col = float3(0.06f, 0.07f, 0.12f);
        col = lerp(col, float3(0.95f, 0.85f, 0.35f), ring);
        col += float3(0.35f, 0.55f, 1.1f) * spokes * saturate(1.f - r) * 0.4f;
        return col;
    }
    if (gChapter == 14)
    {
        // BoS shaping — y = pow(x,3) plot line
        float2 st = uv;
        st.y = 1.f - st.y;
        float y = pow(st.x, 3.f);
        float3 color = float3(y, y, y) * 0.85f;
        float pct = smoothstep(y - 0.02f, y, st.y) - smoothstep(y, y + 0.02f, st.y);
        color = (1.f - pct) * color + pct * float3(0.25f, 0.95f, 0.55f);
        return color;
    }
    // Ch15 BoS patterns — tiled soft circles
    {
        float2 grid = uv * 6.f;
        float2 cell = floor(grid);
        float2 f = frac(grid);
        float2 p = f * 2.f - 1.f;
        float rad = 0.35f + 0.08f * sin(gTime * 1.7f + cell.x * 0.7f + cell.y * 1.1f);
        float d = length(p) - rad;
        float mask = 1.f - smoothstep(-0.02f, 0.02f, d);
        float checker = fmod(cell.x + cell.y, 2.f);
        float3 ink = lerp(float3(0.2f, 0.55f, 0.9f), float3(0.85f, 0.4f, 0.75f), checker);
        return lerp(float3(0.05f, 0.06f, 0.09f), ink, mask);
    }
}

// World-scale look UVs — 1 unit ≈ 1 world meter (triplanar by dominant normal).
float2 worldScaleUv(float3 posW, float3 N)
{
    float3 a = abs(N);
    float2 uv;
    if (a.y >= a.x && a.y >= a.z)
        uv = posW.xz;
    else if (a.x >= a.z)
        uv = posW.zy;
    else
        uv = posW.xy;
    return frac(uv);
}

// Iteration 6 lighting modes — Unlit raw look, or shade look-as-albedo with temple sun.
float3 applyLightMode(float3 look, float3 N, float3 V)
{
    if (gLightMode == 0)
        return look;
    if (gLightMode == 1)
        return shadeLambert(N, look);
    if (gLightMode == 2)
        return shadeBlinn(N, V, look);
    return shadePhysical(N, V, look, 0.32f, 0.08f);
}

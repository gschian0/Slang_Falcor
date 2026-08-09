// VERNACULAR — Temple of Secret Knowledge (Iteration 3) + pinned Vibration Modes.
// Analytic raster only (no alphaTest / material-eval).
// Show mode: gShowMode 0 = TempleSchool, 1 = VibrationModes
import Scene.Raster;

cbuffer PerFrameCB
{
    uint gShowMode;      // 0 temple, 1 vibration
    uint gChapter;
    float gTime;
    float gVibeAmp;
    uint gVertexWaves;
    uint gMatFloor;
    uint gMatCube;
    uint gMatLetter;
    uint gMatSky;
    uint gMatOcean;
    uint gMatLand;
    uint gMatCanvas;
    float gSunElev;
    float gSunAzim;
    float gCloudCover;
    float gFogDensity;
    float gFogHeight;
    float gExposure;
    float gSkyIntensity;
    float gWaterScale;
    float gWaterChop;
    float gWaterAbsorb;
    float3 gWaterColor;
    float gPadW;
};

float hash11(float n)
{
    return frac(sin(n) * 43758.5453123f);
}

float2 hash21n(float n)
{
    return float2(hash11(n), hash11(n + 19.19f));
}

float hash21(float2 p)
{
    float3 p3 = frac(float3(p.xyx) * 0.1031f);
    p3 += dot(p3, p3.yzx + 33.33f);
    return frac((p3.x + p3.y) * p3.z);
}

float3 hash31(float n)
{
    return float3(hash11(n), hash11(n + 7.7f), hash11(n + 13.13f));
}

// shading_ladder uses hash21(float) — alias
float2 hash21(float n)
{
    return hash21n(n);
}

float valueNoise(float2 p)
{
    float2 i = floor(p);
    float2 f = frac(p);
    float2 u = f * f * (3.f - 2.f * f);
    float a = hash21(i);
    float b = hash21(i + float2(1, 0));
    float c = hash21(i + float2(0, 1));
    float d = hash21(i + float2(1, 1));
    return lerp(lerp(a, b, u.x), lerp(c, d, u.x), u.y);
}

float fbm(float2 p)
{
    float v = 0.f;
    float a = 0.5f;
    [unroll]
    for (int i = 0; i < 5; i++)
    {
        v += a * valueNoise(p);
        p = mul(float2x2(1.6f, 1.2f, -1.2f, 1.6f), p) + 17.1f;
        a *= 0.5f;
    }
    return v;
}

// Standing-wave amplitude — Vibration Modes panels (Iteration 2, pinned).
float vibrationMode(float3 posW, float t, out int2 modeOut)
{
    float panel = round(posW.x / 4.0f);
    int nx = 1;
    int ny = 1;
    if (panel <= -1.5f)
    {
        nx = 1;
        ny = 1;
    }
    else if (panel <= -0.5f)
    {
        nx = 2;
        ny = 1;
    }
    else if (panel <= 0.5f)
    {
        nx = 1;
        ny = 2;
    }
    else
    {
        nx = 2;
        ny = 2;
    }
    modeOut = int2(nx, ny);

    float cx = panel * 4.0f;
    float u = saturate((posW.x - (cx - 1.2f)) / 2.4f);
    float v = saturate((posW.z + 1.2f) / 2.4f);

    if (posW.z < -2.5f)
    {
        modeOut = int2(3, 1);
        return sin(3.14159265f * 3.0f * saturate((posW.x + 8.f) / 16.f)) * sin(gTime * 3.2f);
    }

    float PI = 3.14159265f;
    float omega = 2.6f + 0.35f * float(nx + ny);
    return sin(PI * float(nx) * u) * sin(PI * float(ny) * v) * sin(omega * t);
}

#include "lessons/shading_ladder.slang"
#include "lessons/temple_env.slang"

VSOut vsMain(VSIn vIn)
{
    VSOut vOut = defaultVS(vIn);

    if (gShowMode == 1)
    {
        if (vOut.materialID == gMatFloor)
            return vOut;
        if (gVertexWaves != 0 && gVibeAmp > 1e-4f)
        {
            int2 modeIgnored;
            float w = vibrationMode(vOut.posW, gTime, modeIgnored);
            float env = (gChapter == 9) ? pow(abs(sin(gTime * 1.7f)), 0.35f) : 1.f;
            float3 n = normalize(vOut.normalW);
            float3 disp = float3(0.f, 1.f, 0.f) * (w * gVibeAmp * env);
            disp += n * (w * gVibeAmp * 0.35f * env);
            float localRipple = 0.15f * sin(12.f * vIn.pos.x + gTime * 4.f) * sin(12.f * vIn.pos.z + gTime * 3.1f);
            disp.y += localRipple * gVibeAmp * env;
            vOut.posW += disp;
            vOut.posH = mul(gScene.camera.getViewProj(), float4(vOut.posW, 1.f));
        }
        return vOut;
    }

    // Temple — flatten ocean grid to water deck (raymarch beauty in PS)
    if (vOut.materialID == gMatOcean)
    {
        vOut.posW.y = min(vOut.posW.y, 0.f);
        vOut.normalW = float3(0.f, 1.f, 0.f);
        vOut.posH = mul(gScene.camera.getViewProj(), float4(vOut.posW, 1.f));
    }
    return vOut;
}

float4 psMain(VSOut vsOut, uint triangleIndex : SV_PrimitiveID) : SV_TARGET
{
    float3 N = normalize(vsOut.normalW);
    float3 V = normalize(gScene.camera.getPosition() - vsOut.posW);
    if (dot(N, V) < 0.f)
        N = -N;
    float2 uv = vsOut.texC;

    // ---- Vibration Modes (Iteration 2, pinned) ----
    if (gShowMode == 1)
    {
        if (vsOut.materialID == gMatFloor)
        {
            float grid = step(0.96f, max(frac(uv.x * 14.f), frac(uv.y * 14.f)));
            float3 col = float3(0.08f, 0.09f, 0.11f) + float3(0.04f, 0.04f, 0.05f) * grid;
            return float4(col, 1.f);
        }
        float3 albedo = float3(0.75f, 0.4f, 0.3f);
        if (vsOut.materialID == gMatLetter)
            albedo = float3(0.92f, 0.88f, 0.72f);
        else
        {
            uint mid = triangleIndex % 3;
            if (mid == 1)
                albedo = float3(0.25f, 0.28f, 0.32f);
            else if (mid == 2)
                albedo = float3(0.3f, 0.55f, 0.8f);
        }
        float3 color = shadeChapterLook(uv, N, V, vsOut.posW, albedo);
        return float4(saturate(color), 1.f);
    }

    // ---- Temple of Secret Knowledge ----
    float3 posW = vsOut.posW;
    float3 cam = gScene.camera.getPosition();
    float3 ray = normalize(posW - cam);
    float3 view = -ray;

    if (vsOut.materialID == gMatSky)
    {
        float3 dir = normalize(posW); // dome centered at origin
        // Prefer camera ray for correct sky projection
        dir = ray;
        float3 hdr = getSkyHdr(dir, gTime);
        float horizon = saturate(1.f - dir.y * 2.5f);
        hdr = lerp(hdr, getSkyHdr(float3(dir.x, 0.08f, dir.z), gTime), horizon * saturate(gFogDensity * 8.f));
        return float4(aces_tonemap(hdr * 2.0f), 1.f);
    }

    if (vsOut.materialID == gMatOcean)
    {
        float3 hdr = oceanRaymarchHdr(cam, ray, gTime);
        float dist = length(posW - cam);
        float haze = saturate(1.f - exp(-gFogDensity * 0.35f * dist));
        hdr = lerp(hdr, getSkyHdr(float3(ray.x, 0.08f, ray.z), gTime), haze * 0.35f);
        return float4(aces_tonemap(hdr * 2.0f), 1.f);
    }

    if (vsOut.materialID == gMatLand)
    {
        if (abs(N.y) < 0.2f)
            N = float3(0, 1, 0);
        float3 hdr = landLook(uv, N, view, posW);
        hdr = applyFog(hdr, posW, cam, ray);
        return float4(aces_tonemap(hdr * 1.8f), 1.f);
    }

    // Hero canvases — plane / sphere / cube share LessonCanvas look
    float3 albedo = float3(0.72f, 0.55f, 0.48f);
    uint mid = triangleIndex % 3;
    if (mid == 1)
        albedo = float3(0.35f, 0.4f, 0.55f);
    else if (mid == 2)
        albedo = float3(0.55f, 0.45f, 0.75f);
    float3 look = shadeChapterLook(uv, N, view, posW, albedo);
    // Soft temple rim so canvases float in haze
    float rim = pow(1.f - saturate(abs(dot(N, view))), 2.6f);
    look += float3(0.35f, 0.55f, 0.95f) * rim * 0.35f;
    look = applyFog(look * 1.4f, posW, cam, ray);
    return float4(aces_tonemap(look), 1.f);
}

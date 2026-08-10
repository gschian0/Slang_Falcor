// VERNACULAR — Temple of Secret Knowledge (Iteration 3) + pinned Vibration Modes.
// Iteration 6: square plane, world-scale UVs, lighting modes, ocean canvas reflections.
// Iteration 7: VS/PS split into lessons/temple_{vs,ps}.slang (school editor) + upscale/TAA host.
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
    uint gLightMode;     // 0 unlit, 1 Lambert, 2 Blinn, 3 Physical
    float3 gPlaneCenter;
    float gPlaneSize;
    float3 gSphereCenter;
    float gSphereRadius;
    float3 gCubeCenter;
    float gCubeSize;
    float3 gCubeRot0;
    float gPadR0;
    float3 gCubeRot1;
    float gPadR1;
    float3 gCubeRot2;
    float gPadR2;
};

// Shared temple sun — sky, ocean specular, canvas lighting (must precede lesson includes).
float3 getSunDirection()
{
    float elev = gSunElev * 1.35f + 0.02f;
    float az = gSunAzim * 6.2831853f;
    return normalize(float3(cos(elev) * sin(az), sin(elev), cos(elev) * cos(az)));
}

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
#include "lessons/temple_vs.slang"
#include "lessons/temple_ps.slang"

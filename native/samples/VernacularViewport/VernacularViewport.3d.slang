// VERNACULAR abstract studio — cube / island / ocean / sky + analytic lesson looks.
// 3D Gaussian network ports labs/.../sp06_gsplat2d.slang (+ NG03 mix idea).
// Analytic only (no alphaTest / material-eval).
import Scene.Raster;

cbuffer PerFrameCB
{
    float gTime;
    uint gFoldMode;
    float gFoldStrength;
    float gMandelLogZoom;
    float2 gJuliaC;
    float2 gMandelCenter;
    float gMandelActivity;
    float gSunElev;
    float gSunAzim;
    float gCloudCover;
    float gFogDensity;
    float gFogHeight;
    float gLightWarm;
    float gLightCool;
    float gExposure;
    float3 gCubePos;
    float gCubeScale;
    float gMorph;
    uint gLessonLook;
    float3 gIslandCenter;
    float gIslandRadius;
    // Gaussian network (pad float3 → 16B)
    uint gGaussCount;
    float gGaussSigma;
    float gGaussAmp;
    float gGaussLayerDepth;
    float gGaussMix;
    float gGaussAnim;
    float2 gGaussPad0;
    float3 gGaussColA;
    float gGaussPadA;
    float3 gGaussColB;
    float gGaussPadB;
    float3 gGaussColC;
    float gGaussPadC;
    float3 gGaussSpread;
    float gGaussPadS;
};

static const float DRAG_MULT = 0.38f;
static const float WATER_DEPTH = 1.0f;

float hash21(float2 p)
{
    float3 p3 = frac(float3(p.xyx) * 0.1031f);
    p3 += dot(p3, p3.yzx + 33.33f);
    return frac((p3.x + p3.y) * p3.z);
}

float hash11(float n)
{
    return frac(sin(n) * 43758.5453123f);
}

float3 hash31(float n)
{
    return float3(hash11(n), hash11(n + 7.7f), hash11(n + 13.13f));
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

float2 wavedx(float2 position, float2 direction, float frequency, float timeshift)
{
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0f);
    float dx = wave * cos(x);
    return float2(wave, -dx);
}

float getwaves(float2 position, float time)
{
    float wavePhaseShift = length(position) * 0.1f;
    float iter = 0.0f;
    float frequency = 1.0f;
    float timeMultiplier = 5.0f;
    float weight = 1.0f;
    float sumOfValues = 0.0f;
    float sumOfWeights = 0.0f;
    [unroll]
    for (int i = 0; i < 12; i++)
    {
        float2 p = float2(sin(iter), cos(iter));
        float2 res = wavedx(position, p, frequency, time * timeMultiplier + wavePhaseShift);
        position += p * res.y * weight * DRAG_MULT;
        sumOfValues += res.x * weight;
        sumOfWeights += weight;
        weight = lerp(weight, 0.0f, 0.2f);
        frequency *= 1.18f;
        timeMultiplier *= 1.07f;
        iter += 1232.399963f;
    }
    return sumOfValues / sumOfWeights;
}

float3 wave_normal(float2 pos, float time)
{
    float e = 0.01f;
    float h = getwaves(pos, time);
    float hx = getwaves(pos + float2(e, 0.0f), time);
    float hz = getwaves(pos + float2(0.0f, e), time);
    return normalize(float3(-(hx - h) / e, 1.0f, -(hz - h) / e));
}

float intersectPlane(float3 origin, float3 direction, float3 point, float3 normal)
{
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0f, 9991999.0f);
}

float raymarchwater(float3 camera, float3 start, float3 end, float depth, float time)
{
    float3 pos = start;
    float3 dir = normalize(end - start);
    for (int i = 0; i < 40; i++)
    {
        float height = getwaves(pos.xz, time) * depth - depth;
        if (height + 0.01f > pos.y)
            return distance(pos, camera);
        pos += dir * (pos.y - height);
    }
    return distance(start, camera);
}

float3 getSunDirection()
{
    float elev = gSunElev * 1.35f + 0.02f;
    float az = gSunAzim * 6.2831853f;
    return normalize(float3(cos(elev) * sin(az), sin(elev), cos(elev) * cos(az)));
}

float3 extra_cheap_atmosphere(float3 raydir, float3 sundir)
{
    sundir.y = max(sundir.y, -0.07f);
    float special_trick = 1.0f / (raydir.y * 1.0f + 0.1f);
    float special_trick2 = 1.0f / (sundir.y * 11.0f + 1.0f);
    float raysundt = pow(abs(dot(sundir, raydir)), 2.0f);
    float sundt = pow(max(0.0f, dot(sundir, raydir)), 8.0f);
    float mymie = sundt * special_trick * 0.2f;
    float3 suncolor = lerp(float3(1, 1, 1), max(float3(0, 0, 0), float3(1, 1, 1) - float3(5.5f, 13.0f, 22.4f) / 22.4f), special_trick2);
    float3 bluesky = float3(5.5f, 13.0f, 22.4f) / 22.4f * suncolor;
    float3 bluesky2 = max(float3(0, 0, 0), bluesky - float3(5.5f, 13.0f, 22.4f) * 0.002f * (special_trick + -6.0f * sundir.y * sundir.y));
    bluesky2 *= special_trick * (0.24f + raysundt * 0.24f);
    return bluesky2 * (1.0f + pow(1.0f - raydir.y, 3.0f)) + float3(mymie, mymie, mymie);
}

float getSunDisk(float3 dir, float3 sundir)
{
    return pow(max(0.0f, dot(dir, sundir)), 720.0f) * 210.0f;
}

float3 cloudLayer(float3 dir, float time)
{
    if (dir.y < 0.02f)
        return float3(0, 0, 0);
    float2 uv = dir.xz / max(0.15f, dir.y + 0.35f);
    uv += float2(time * 0.012f, time * 0.007f);
    float n = fbm(uv * 2.2f);
    float n2 = fbm(uv * 5.5f + 19.f);
    float cover = lerp(0.55f, 0.14f, saturate(gCloudCover));
    float dens = smoothstep(cover, cover + 0.32f, n) * saturate(gCloudCover * 1.55f);
    dens *= 0.65f + 0.35f * n2;
    dens *= smoothstep(0.02f, 0.28f, dir.y);
    float3 sundir = getSunDirection();
    float silver = pow(saturate(dot(normalize(dir + sundir * 0.2f), sundir)), 6.f);
    float3 cloudCol = lerp(float3(0.45f, 0.52f, 0.68f), float3(1.15f, 0.95f, 0.78f), silver);
    cloudCol = lerp(cloudCol, float3(1.35f, 0.45f, 0.18f), saturate(0.25f - sundir.y) * dens);
    return cloudCol * dens * 1.55f;
}

float3 getSkyHdr(float3 dir, float time)
{
    float3 sundir = getSunDirection();
    float3 sky = extra_cheap_atmosphere(dir, sundir) * 0.5f;
    sky += getSunDisk(dir, sundir);
    sky += cloudLayer(dir, time);
    return sky;
}

float3 aces_tonemap(float3 color)
{
    float3 x = color * 0.6f * max(0.1f, gExposure);
    float3 a = x * (x + 0.0245786f) - 0.000090537f;
    float3 b = x * (0.983729f * x + 0.4329510f) + 0.238081f;
    return pow(saturate(a / b), 1.0f / 2.2f);
}

float3 applyFog(float3 color, float3 posW, float3 cam, float3 ray)
{
    float dist = length(posW - cam);
    float h = max(posW.y, 0.f);
    float heightFactor = exp(-h * max(0.01f, gFogHeight));
    float fog = saturate(1.f - exp(-gFogDensity * dist * heightFactor));
    float3 sundir = getSunDirection();
    float3 fogCol = getSkyHdr(float3(ray.x, max(0.05f, abs(ray.y) * 0.35f), ray.z), gTime);
    fogCol = lerp(fogCol, float3(0.55f, 0.7f, 0.95f), 0.35f);
    fogCol += float3(1.0f, 0.85f, 0.55f) * pow(saturate(dot(normalize(ray), sundir)), 6.f) * 0.35f * fog;
    return lerp(color, fogCol, fog);
}

float2 cMul(float2 a, float2 b)
{
    return float2(a.x * b.x - a.y * b.y, a.x * b.y + a.y * b.x);
}

float2 boxFold(float2 z, float limit)
{
    return clamp(z, -limit, limit) * 2.f - z;
}

struct FoldResult
{
    float2 ndc;
    float energy;
};

FoldResult foldJulia(float2 ndc)
{
    float2 z = ndc * 1.35f;
    float2 c = gJuliaC;
    float escape = 0.f;
    [unroll]
    for (int i = 0; i < 16; i++)
    {
        z = boxFold(z, 1.15f);
        z = cMul(z, z) + c;
        if (dot(z, z) > 16.f)
        {
            escape = float(i) / 16.f;
            break;
        }
        escape = float(i) / 16.f;
    }
    FoldResult r;
    r.ndc = lerp(ndc, z * 0.22f, gFoldStrength);
    r.energy = escape;
    return r;
}

FoldResult foldMandelbrot(float2 ndc)
{
    float zoom = pow(10.f, gMandelLogZoom);
    float2 uv = ndc;
    uv.x *= 1.6f;
    float2 c = gMandelCenter + uv / zoom;
    float2 z = float2(0, 0);
    int last = 0;
    [unroll]
    for (int i = 0; i < 24; i++)
    {
        z = cMul(z, z) + c;
        if (gMandelActivity > 0.2f)
            z = boxFold(z, 1.4f + gMandelActivity) * (0.85f + 0.2f * gMandelActivity);
        if (dot(z, z) > 16.f)
        {
            last = i;
            break;
        }
        last = i;
    }
    float escape = float(last) / 24.f;
    float2 warped = normalize(z + 1e-5f) * (0.35f + escape) * (0.6f + 0.8f * gMandelActivity);
    FoldResult r;
    r.ndc = lerp(ndc, warped, gFoldStrength * (0.55f + 0.45f * gMandelActivity));
    r.energy = escape;
    return r;
}

FoldResult applyViewportFold(float2 ndc)
{
    FoldResult r;
    r.ndc = ndc;
    r.energy = 0.f;
    if (gFoldMode == 1)
        r = foldJulia(ndc);
    else if (gFoldMode == 2)
        r = foldMandelbrot(ndc);
    return r;
}

float3 foldPalette(float e)
{
    float3 col = lerp(float3(0.02f, 0.05f, 0.15f), float3(0.1f, 0.9f, 0.85f), saturate(e * 1.4f));
    return lerp(col, float3(1.f, 0.35f, 0.05f), saturate(e * e * 2.f));
}

// 0 sky · 1 ocean · 4 distant land · 5 morph cube · 6 island
uint classifyWorld(float3 posW)
{
    if (length(posW) > 55.f)
        return 0;

    float cubeR = max(0.6f, gCubeScale) * 1.15f;
    if (length(posW - gCubePos) < cubeR)
        return 5;

    float2 dIsl = posW.xz - gIslandCenter.xz;
    float islR = max(4.f, gIslandRadius);
    if (dot(dIsl, dIsl) < islR * islR && posW.y > -0.4f && posW.y < 3.5f)
        return 6;

    // Distant land / hills (beyond the water ring)
    if (posW.y > -0.5f && posW.y < 18.f && length(posW.xz) > islR + 8.f && abs(posW.z) > 40.f)
        return 4;
    if (posW.y > 1.5f && posW.y < 18.f && length(posW.xz) > 45.f)
        return 4;

    // Ocean frames the island
    if (posW.y < 2.5f)
        return 1;

    return 0;
}

VSOut vsMain(VSIn vIn)
{
    VSOut vOut = defaultVS(vIn);
    // Ocean grid = flat deck at y≈0; beauty is raymarched in PS
    float mxy = max(abs(vIn.pos.x), abs(vIn.pos.y));
    if (mxy > 2.f && abs(vIn.pos.z) < 0.05f)
    {
        vOut.posW.y = min(vOut.posW.y, 0.f);
        vOut.normalW = float3(0.f, 1.f, 0.f);
        vOut.posH = mul(gScene.camera.getViewProj(), float4(vOut.posW, 1.f));
    }
    // Morph cube — fine vertex ripples
    float3 toC = vOut.posW - gCubePos;
    if (length(toC) < max(0.6f, gCubeScale) * 1.25f)
    {
        float n = sin(dot(vOut.posW, float3(2.1f, 3.3f, 1.7f)) + gTime * 3.5f);
        float wobble = n * 0.045f * gMorph;
        vOut.posW += normalize(toC + 1e-4f) * wobble;
        vOut.posH = mul(gScene.camera.getViewProj(), float4(vOut.posW, 1.f));
    }
    return vOut;
}

float3 bendViewDir(float3 viewDir, float2 foldNdc)
{
    float3 fwd = normalize(viewDir);
    float3 up = float3(0, 1, 0);
    float3 right = normalize(cross(fwd, up));
    up = normalize(cross(right, fwd));
    return normalize(fwd + right * foldNdc.x * 1.25f + up * foldNdc.y * 1.25f);
}

float3 accentLights(float3 posW, float3 N, float3 V)
{
    float3 warmDir = normalize(float3(0.55f, 0.35f, 0.2f));
    float3 coolDir = normalize(float3(-0.4f, 0.55f, -0.65f));
    float3 glowPos = float3(sin(gTime * 0.4f) * 6.f, 2.2f + 0.4f * sin(gTime * 0.7f), 4.f + cos(gTime * 0.33f) * 3.f);
    float3 toGlow = glowPos - posW;
    float glowAtt = 1.f / (1.f + dot(toGlow, toGlow) * 0.04f);
    float3 glowDir = normalize(toGlow);
    float3 warm = float3(1.0f, 0.55f, 0.22f) * saturate(dot(N, warmDir)) * gLightWarm;
    float3 cool = float3(0.25f, 0.55f, 1.15f) * pow(saturate(1.f - abs(dot(N, V))), 2.5f) * gLightCool;
    float3 pulse = float3(0.4f, 1.0f, 0.85f) * saturate(dot(N, glowDir)) * glowAtt * (0.35f + 0.65f * gLightCool);
    float3 H = normalize(warmDir + V);
    warm += float3(1.0f, 0.85f, 0.55f) * pow(saturate(dot(N, H)), 64.f) * gLightWarm * 0.8f;
    return warm + cool + pulse;
}

float3 oceanRaymarchHdr(float3 cam, float3 ray, float time)
{
    if (ray.y >= 0.02f)
        return getSkyHdr(ray, time);

    float3 origin = cam;
    float3 waterPlaneHigh = float3(0.0f, 0.0f, 0.0f);
    float3 waterPlaneLow = float3(0.0f, -WATER_DEPTH, 0.0f);
    float highPlaneHit = intersectPlane(origin, ray, waterPlaneHigh, float3(0.0f, 1.0f, 0.0f));
    float lowPlaneHit = intersectPlane(origin, ray, waterPlaneLow, float3(0.0f, 1.0f, 0.0f));
    float3 highHitPos = origin + ray * highPlaneHit;
    float3 lowHitPos = origin + ray * lowPlaneHit;

    float dist = raymarchwater(origin, highHitPos, lowHitPos, WATER_DEPTH, time);
    float3 waterHitPos = origin + ray * dist;
    float3 N = wave_normal(waterHitPos.xz, time);
    float interpFactor = 0.8f * min(1.0f, sqrt(dist * 0.01f) * 1.1f);
    N = lerp(N, float3(0.0f, 1.0f, 0.0f), interpFactor);

    float fresnel = 0.04f + 0.96f * pow(1.0f - max(0.0f, dot(-N, ray)), 5.0f);
    float3 R = normalize(reflect(ray, N));
    R.y = abs(R.y);

    float3 sundir = getSunDirection();
    float3 reflection = extra_cheap_atmosphere(R, sundir) * 0.5f + getSunDisk(R, sundir);
    reflection += cloudLayer(R, time) * 0.65f;

    float3 scattering = float3(0.0293f, 0.0698f, 0.1717f) * 0.1f
                        * (0.2f + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);
    return fresnel * reflection + scattering;
}

float3 landLook(float2 uv, float3 N, float3 V, float3 posW)
{
    float h = posW.y;
    float n = fbm(posW.xz * 0.08f);
    float n2 = fbm(posW.xz * 0.35f + 9.f);
    float3 sand = float3(0.62f, 0.52f, 0.32f);
    float3 grass = float3(0.22f, 0.42f, 0.18f);
    float3 rock = float3(0.38f, 0.36f, 0.34f);
    float3 dirt = float3(0.35f, 0.28f, 0.18f);
    float3 col = lerp(sand, grass, saturate(n * 0.85f));
    col = lerp(col, rock, smoothstep(2.5f, 7.f, h) * (0.4f + 0.6f * n2));
    col = lerp(col, dirt, (1.f - saturate(h * 0.35f)) * 0.35f);
    float ndl = saturate(dot(normalize(N), getSunDirection()));
    col *= 0.25f + 0.75f * ndl;
    col += accentLights(posW, normalize(N), V) * 0.2f;
    return col * 1.35f;
}

// Island surface — terrain + optional Gaussian tint when lesson look == 4
float3 islandLook(float2 uv, float3 N, float3 V, float3 posW)
{
    float2 p = (posW.xz - gIslandCenter.xz) / max(4.f, gIslandRadius);
    float r = length(p);
    float n = fbm(posW.xz * 0.12f);
    float n2 = fbm(posW.xz * 0.45f + 5.f);
    float3 beach = float3(0.72f, 0.62f, 0.42f);
    float3 grass = float3(0.28f, 0.48f, 0.22f);
    float3 moss = float3(0.18f, 0.38f, 0.2f);
    float shore = smoothstep(0.55f, 0.95f, r);
    float3 col = lerp(grass, moss, n * 0.55f);
    col = lerp(col, beach, shore * (0.55f + 0.45f * n2));
    // Soft height ripples so the island isn't a flat card
    float bump = 0.08f * n + 0.04f * sin(posW.x * 0.4f + gTime * 0.2f);
    col *= 0.85f + 0.2f * bump;

    if (gLessonLook == 4)
    {
        // Projected soft Gaussians tint the island — same network family as the cube
        float3 tint = float3(0, 0, 0);
        float sigma = max(0.04f, gGaussSigma * 1.8f);
        uint count = min(8u, max(1u, gGaussCount));
        [unroll]
        for (uint i = 0; i < 8; i++)
        {
            if (i >= count)
                break;
            float id = float(i) + 1.f;
            float2 c = float2(hash11(id * 12.9898f), hash11(id * 78.233f)) * 2.f - 1.f;
            c *= 0.55f;
            c += gGaussAnim * 0.08f * float2(sin(gTime * 0.55f + id), cos(gTime * 0.41f + id * 1.3f));
            float2 d = (p - c) / (sigma * float2(gGaussSpread.x, gGaussSpread.z));
            float w = exp(-dot(d, d));
            float3 blobCol = (i % 3u == 0u) ? gGaussColA : ((i % 3u == 1u) ? gGaussColB : gGaussColC);
            tint += blobCol * w * gGaussAmp * 0.35f;
        }
        col = lerp(col, saturate(col * 0.35f + tint), saturate(gGaussMix));
    }

    float ndl = saturate(dot(normalize(N), getSunDirection()));
    col *= 0.3f + 0.7f * ndl;
    col += accentLights(posW, normalize(N), V) * 0.25f;
    float foam = smoothstep(0.72f, 1.05f, r);
    col = lerp(col, float3(0.85f, 0.9f, 0.95f), foam * 0.4f * (0.5f + 0.5f * sin(gTime * 2.f + posW.x)));
    return col * 1.45f;
}

// sp06-style eval: weight = exp(-r²/(2σ²)), alpha-composited in RGB
float4 evalGauss3(float3 p, float3 center, float3 sigma, float3 color)
{
    float3 d = (p - center) / max(sigma, float3(1e-3f, 1e-3f, 1e-3f));
    float weight = exp(-0.5f * dot(d, d));
    return float4(color, weight);
}

float4 alphaBlend(float4 pixel, float4 gval)
{
    float4 p = float4(gval.rgb * gval.a, gval.a);
    return float4(pixel.rgb + p.rgb * pixel.a, pixel.a * (1.0f - p.a));
}

// Tiny weighted Gaussian mixture / "network" on the cube face (3D field + UV project)
float3 gaussianNetworkLook(float2 uv, float3 N, float3 V, float3 posW)
{
    float2 p2 = uv * 2.f - 1.f;
    // Local 3D sample around the cube face: UV + depth along normal (layer network)
    float3 p = float3(p2.x, p2.y, 0.f);
    float t = gTime * max(0.05f, gGaussAnim);

    float3 sigmaBase = max(0.04f, gGaussSigma) * max(gGaussSpread, float3(0.2f, 0.2f, 0.2f));
    uint count = min(8u, max(1u, gGaussCount));

    float4 accum = float4(0.0f, 0.0f, 0.0f, 1.0f);
    float3 energy = float3(0, 0, 0);

    [unroll]
    for (uint i = 0; i < 8; i++)
    {
        if (i >= count)
            break;
        float id = float(i) + 1.f;
        // Parameterizable centers: hash seed + orbit animation + layer depth stack
        float3 center;
        center.x = (hash11(id * 12.9898f) * 2.f - 1.f) * 0.72f;
        center.y = (hash11(id * 78.233f) * 2.f - 1.f) * 0.72f;
        center.z = ((float(i) / max(1.f, float(count - 1u))) - 0.5f) * gGaussLayerDepth;
        center.xy += gGaussAnim * 0.12f * float2(sin(t * 0.7f + id), cos(t * 0.5f + id * 1.3f));
        center.z += 0.08f * sin(t * 0.9f + id * 2.1f) * gGaussLayerDepth;

        float sigmaJitter = 0.65f + 0.55f * hash11(id * 3.1f);
        float3 sigma = sigmaBase * sigmaJitter;

        float3 blobCol = (i % 3u == 0u) ? gGaussColA : ((i % 3u == 1u) ? gGaussColB : gGaussColC);
        blobCol = lerp(blobCol, hash31(id * 5.5f), 0.15f);

        // Mix weight — soft "network" gain per node
        float nodeW = lerp(0.55f, 1.25f, hash11(id * 9.7f)) * gGaussAmp * gGaussMix;

        float4 gval = evalGauss3(p, center, sigma, blobCol * nodeW);
        accum = alphaBlend(accum, gval);
        energy += blobCol * gval.a * nodeW;

        // Second "layer" slightly along the surface normal in screen-ish space
        float3 pDeep = p + float3(0, 0, 0.35f * gGaussLayerDepth);
        float4 g2 = evalGauss3(pDeep, center, sigma * 1.15f, blobCol * nodeW * 0.55f);
        accum = alphaBlend(accum, g2);
    }

    float3 bg = float3(0.04f, 0.05f, 0.08f);
    float3 col = accum.rgb * (1.0f - accum.a) + bg * accum.a;
    // Additive mixture tail (NG03-style sum of splats) blended in
    col = lerp(col, saturate(bg + energy * 0.55f), 0.35f * gGaussMix);

    // Soft grid so it still reads as "shader on a cube"
    float grid = step(0.94f, max(frac(uv.x * 6.f), frac(uv.y * 6.f)));
    col = lerp(col, col * 1.25f + 0.08f, grid * 0.35f);

    float rim = pow(1.f - saturate(abs(dot(normalize(N), V))), 2.4f);
    col += float3(0.35f, 0.85f, 1.15f) * rim * (0.45f + gLightCool * 0.35f);
    col += accentLights(posW, normalize(N), V) * 0.3f;
    return col * 1.75f;
}

float3 morphCubeLesson(float2 uv, float3 N, float3 V, float3 posW)
{
    float2 p = uv * 2.f - 1.f;
    float t = gTime;
    float3 col;

    if (gLessonLook == 4)
        return gaussianNetworkLook(uv, N, V, posW);

    if (gLessonLook == 1)
    {
        float w = getwaves(posW.xz * 0.35f + uv * 3.f, t);
        float3 wn = wave_normal(uv * 4.f + posW.xz * 0.2f, t);
        float fres = 0.04f + 0.96f * pow(1.f - saturate(abs(dot(wn, V))), 5.f);
        col = float3(0.02f, 0.12f, 0.28f) + fres * getSkyHdr(reflect(-V, wn), t) * 0.45f;
        col += float3(0.05f, 0.25f, 0.45f) * w;
    }
    else if (gLessonLook == 2)
    {
        float bands = 0.5f + 0.5f * sin(p.x * 14.f + t * 2.2f) * cos(p.y * 11.f - t * 1.9f);
        float plasma = 0.5f + 0.5f * sin(length(p) * 9.f - t * 3.2f + bands * 5.f);
        col = lerp(float3(0.05f, 0.1f, 0.35f), float3(1.15f, 0.25f, 0.75f), plasma);
        col = lerp(col, float3(0.1f, 1.0f, 0.85f), bands * 0.45f);
    }
    else if (gLessonLook == 3)
    {
        float r = length(p);
        float a = atan2(p.y, p.x);
        float ring = smoothstep(0.08f, 0.02f, abs(r - (0.55f + 0.08f * sin(t * 2.f))));
        float spokes = 0.5f + 0.5f * sin(a * 6.f + t);
        col = float3(0.08f, 0.08f, 0.12f);
        col = lerp(col, float3(0.95f, 0.85f, 0.25f), ring);
        col += float3(0.2f, 0.55f, 1.1f) * spokes * saturate(1.f - r) * 0.35f;
    }
    else
    {
        col = float3(uv.x, uv.y, 0.35f + 0.4f * sin(t + uv.x * 6.f));
        float grid = step(0.94f, max(frac(uv.x * 8.f), frac(uv.y * 8.f)));
        col = lerp(col, float3(1.2f, 1.2f, 1.2f), grid * 0.5f);
    }

    float morphPulse = saturate(gMorph);
    float2 z = p * (1.2f + morphPulse);
    float esc = 0.f;
    [unroll]
    for (int i = 0; i < 8; i++)
    {
        z = float2(z.x * z.x - z.y * z.y, 2.f * z.x * z.y) + float2(-0.65f + 0.1f * sin(t * 0.4f), 0.3f);
        if (dot(z, z) > 8.f)
        {
            esc = float(i) / 8.f;
            break;
        }
        esc = float(i) / 8.f;
    }
    col = lerp(col, foldPalette(esc) * 1.4f, morphPulse * 0.35f);

    float rim = pow(1.f - saturate(abs(dot(normalize(N), V))), 2.4f);
    col += float3(0.4f, 0.9f, 1.2f) * rim * (0.5f + gLightCool * 0.4f);
    col += accentLights(posW, normalize(N), V) * 0.35f;
    return col * 1.7f;
}

float4 psMain(VSOut vsOut, uint triangleIndex : SV_PrimitiveID) : SV_TARGET
{
    float3 posW = vsOut.posW;
    float3 cam = gScene.camera.getPosition();
    float3 ray = normalize(posW - cam);
    float3 V = -ray;

    float2 screen = float2(dot(ray, float3(1, 0, 0)) * 1.777f, dot(ray, float3(0, 1, 0)));
    FoldResult fold = applyViewportFold(screen * 1.1f);

    uint obj = classifyWorld(posW);

    float3 hdr;
    if (obj == 0)
    {
        float3 dir = bendViewDir(ray, fold.ndc);
        hdr = getSkyHdr(dir, gTime);
        float horizon = saturate(1.f - dir.y * 2.5f);
        hdr = lerp(hdr, getSkyHdr(float3(dir.x, 0.08f, dir.z), gTime), horizon * saturate(gFogDensity * 8.f));
    }
    else if (obj == 1)
    {
        hdr = oceanRaymarchHdr(cam, ray, gTime);
        float dist = length(posW - cam);
        float haze = saturate(1.f - exp(-gFogDensity * 0.35f * dist));
        hdr = lerp(hdr, getSkyHdr(float3(ray.x, 0.08f, ray.z), gTime), haze * 0.35f);
    }
    else if (obj == 4)
    {
        float3 N = normalize(vsOut.normalW);
        if (dot(N, V) < 0.f)
            N = -N;
        if (abs(N.y) < 0.2f)
            N = float3(0, 1, 0);
        hdr = landLook(vsOut.texC, N, V, posW);
        hdr = applyFog(hdr, posW, cam, ray);
    }
    else if (obj == 6)
    {
        float3 N = normalize(vsOut.normalW);
        if (dot(N, V) < 0.f)
            N = -N;
        if (abs(N.y) < 0.35f)
            N = float3(0, 1, 0);
        hdr = islandLook(vsOut.texC, N, V, posW);
        hdr = applyFog(hdr, posW, cam, ray);
    }
    else
    {
        float3 N = normalize(vsOut.normalW);
        if (dot(N, V) < 0.f)
            N = -N;
        hdr = morphCubeLesson(vsOut.texC, N, V, posW);
        hdr = applyFog(hdr, posW, cam, ray);
    }

    if (gFoldMode != 0)
        hdr = lerp(hdr, foldPalette(fold.energy) * 2.f, 0.12f * gFoldStrength);
    if (gFoldMode == 2 && gMandelActivity > 0.05f)
        hdr += foldPalette(fold.energy) * (0.25f * gMandelActivity);

    return float4(aces_tonemap(hdr * 2.0f), 1.f);
}

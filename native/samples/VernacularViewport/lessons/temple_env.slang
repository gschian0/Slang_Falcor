// VERNACULAR temple environment — ethereal ocean / FBM land / sky.
// Spirit of labs/slang_playground/shaders/sp03_ocean.slang (afl_ext / ShaderToy MdXyzX)
// and Iteration 1 VernacularViewport studio. Expects PerFrameCB env/water fields + hash/fbm.

static const float kWaterDepth = 1.0f;
static const float kDragMult = 0.38f;

float2 wavedx(float2 position, float2 direction, float frequency, float timeshift)
{
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0f);
    float dx = wave * cos(x);
    return float2(wave, -dx);
}

float getwaves(float2 position, float time, float chop)
{
    float wavePhaseShift = length(position) * 0.1f;
    float iter = 0.0f;
    float frequency = 1.0f;
    float timeMultiplier = 5.0f;
    float weight = 1.0f;
    float sumOfValues = 0.0f;
    float sumOfWeights = 0.0f;
    float drag = kDragMult * saturate(0.35f + chop);
    [unroll]
    for (int i = 0; i < 12; i++)
    {
        float2 p = float2(sin(iter), cos(iter));
        float2 res = wavedx(position, p, frequency, time * timeMultiplier + wavePhaseShift);
        position += p * res.y * weight * drag;
        sumOfValues += res.x * weight;
        sumOfWeights += weight;
        weight = lerp(weight, 0.0f, 0.2f);
        frequency *= 1.18f;
        timeMultiplier *= 1.07f;
        iter += 1232.399963f;
    }
    return sumOfValues / sumOfWeights;
}

float3 wave_normal(float2 pos, float time, float chop)
{
    float e = 0.01f;
    float h = getwaves(pos, time, chop);
    float hx = getwaves(pos + float2(e, 0.0f), time, chop);
    float hz = getwaves(pos + float2(0.0f, e), time, chop);
    return normalize(float3(-(hx - h) / e, 1.f, -(hz - h) / e));
}

float intersectPlane(float3 origin, float3 direction, float3 point, float3 normal)
{
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0f, 9991999.0f);
}

float raymarchwater(float3 camera, float3 start, float3 end, float depth, float time, float chop)
{
    float3 pos = start;
    float3 dir = normalize(end - start);
    for (int i = 0; i < 40; i++)
    {
        float height = getwaves(pos.xz, time, chop) * depth - depth;
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
    // Ethereal cool bias — temple haze, not cartoon day
    bluesky2 = lerp(bluesky2, float3(0.35f, 0.42f, 0.72f) * length(bluesky2), 0.28f);
    return bluesky2 * (1.0f + pow(1.0f - raydir.y, 3.0f)) + float3(mymie, mymie, mymie);
}

float getSunDisk(float3 dir, float3 sundir)
{
    return pow(max(0.0f, dot(dir, sundir)), 720.0f) * 180.0f * gSkyIntensity;
}

float3 cloudLayer(float3 dir, float time)
{
    if (dir.y < 0.02f)
        return float3(0, 0, 0);
    float2 uv = dir.xz / max(0.15f, dir.y + 0.35f);
    uv += float2(time * 0.010f, time * 0.006f);
    float n = fbm(uv * 2.0f);
    float n2 = fbm(uv * 5.2f + 19.f);
    float cover = lerp(0.55f, 0.14f, saturate(gCloudCover));
    float dens = smoothstep(cover, cover + 0.32f, n) * saturate(gCloudCover * 1.55f);
    dens *= 0.65f + 0.35f * n2;
    dens *= smoothstep(0.02f, 0.28f, dir.y);
    float3 sundir = getSunDirection();
    float silver = pow(saturate(dot(normalize(dir + sundir * 0.2f), sundir)), 6.f);
    float3 cloudCol = lerp(float3(0.42f, 0.48f, 0.72f), float3(1.05f, 0.92f, 0.82f), silver);
    cloudCol = lerp(cloudCol, float3(0.85f, 0.55f, 0.95f), 0.12f); // soft violet edge
    return cloudCol * dens * 1.35f * gSkyIntensity;
}

float3 getSkyHdr(float3 dir, float time)
{
    float3 sundir = getSunDirection();
    float3 sky = extra_cheap_atmosphere(dir, sundir) * 0.45f * gSkyIntensity;
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
    fogCol = lerp(fogCol, float3(0.45f, 0.55f, 0.85f), 0.4f);
    fogCol += float3(0.85f, 0.75f, 1.0f) * pow(saturate(dot(normalize(ray), sundir)), 6.f) * 0.25f * fog;
    return lerp(color, fogCol, fog);
}

float3 oceanRaymarchHdr(float3 cam, float3 ray, float time)
{
    if (ray.y >= 0.02f)
        return getSkyHdr(ray, time);

    float depth = kWaterDepth;
    float3 origin = cam;
    float3 waterPlaneHigh = float3(0.0f, 0.0f, 0.0f);
    float3 waterPlaneLow = float3(0.0f, -depth, 0.0f);
    float highPlaneHit = intersectPlane(origin, ray, waterPlaneHigh, float3(0.0f, 1.0f, 0.0f));
    float lowPlaneHit = intersectPlane(origin, ray, waterPlaneLow, float3(0.0f, 1.0f, 0.0f));
    float3 highHitPos = origin + ray * highPlaneHit;
    float3 lowHitPos = origin + ray * lowPlaneHit;

    float chop = gWaterChop;
    float scale = max(0.15f, gWaterScale);
    float dist = raymarchwater(origin, highHitPos, lowHitPos, depth, time, chop);
    float3 waterHitPos = origin + ray * dist;
    float3 N = wave_normal(waterHitPos.xz * scale, time, chop);
    float interpFactor = 0.8f * min(1.0f, sqrt(dist * 0.01f) * 1.1f);
    N = lerp(N, float3(0.0f, 1.0f, 0.0f), interpFactor);

    float fresnel = 0.04f + 0.96f * pow(1.0f - max(0.0f, dot(-N, ray)), 5.0f);
    float3 R = normalize(reflect(ray, N));
    R.y = abs(R.y);

    float3 sundir = getSunDirection();
    float3 reflection = extra_cheap_atmosphere(R, sundir) * 0.45f * gSkyIntensity + getSunDisk(R, sundir);
    reflection += cloudLayer(R, time) * 0.55f;

    float3 absorb = gWaterColor * (0.08f + 0.12f * gWaterAbsorb);
    float3 scattering = absorb * (0.2f + (waterHitPos.y + depth) / depth);
    // Soft sacred shimmer
    scattering += float3(0.04f, 0.06f, 0.12f) * (0.5f + 0.5f * sin(time * 0.4f + waterHitPos.x * 0.05f));
    return fresnel * reflection + scattering;
}

// Computer-FBM distant land — weird hills / cliffs, ethereal cool rock.
float3 landLook(float2 uv, float3 N, float3 V, float3 posW)
{
    float h = posW.y;
    float n = fbm(posW.xz * 0.07f);
    float n2 = fbm(posW.xz * 0.28f + 11.f);
    float n3 = fbm(posW.xz * 0.9f + 3.f);
    float3 sand = float3(0.42f, 0.38f, 0.48f);
    float3 moss = float3(0.18f, 0.32f, 0.28f);
    float3 rock = float3(0.28f, 0.30f, 0.38f);
    float3 cliff = float3(0.22f, 0.18f, 0.28f);
    float3 col = lerp(sand, moss, saturate(n * 0.9f));
    col = lerp(col, rock, smoothstep(1.5f, 8.f, h) * (0.35f + 0.65f * n2));
    col = lerp(col, cliff, saturate(n3 * n2) * smoothstep(3.f, 12.f, h));
    // Soft hex-ish sacred geometry whisper
    float2 cell = floor(posW.xz * 0.15f);
    float hex = step(0.92f, abs(sin(cell.x * 2.1f) * cos(cell.y * 1.7f)));
    col = lerp(col, col * float3(1.15f, 1.05f, 1.35f), hex * 0.25f);
    float ndl = saturate(dot(normalize(N), getSunDirection()));
    col *= 0.22f + 0.78f * ndl;
    float rim = pow(1.f - saturate(abs(dot(normalize(N), V))), 2.5f);
    col += float3(0.35f, 0.45f, 0.75f) * rim * 0.35f;
    return col * 1.25f;
}

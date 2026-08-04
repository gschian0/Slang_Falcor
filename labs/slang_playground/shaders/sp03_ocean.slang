// SPDX-License-Identifier: Apache-2.0
// Port of Slang Playground "ShaderToy: Ocean" demo (autodiff normals).
// Upstream: https://github.com/shader-slang/slang-playground/blob/main/public/demos/ocean.slang
// Playground: https://shader-slang.org/slang-playground/
// Ocean by afl_ext — https://www.shadertoy.com/view/MdXyzX (MIT).
// Playground uses bwd_diff(getwaves); here normals use finite differences on the
// same [Differentiable] wave field so hello_pixel stays single-dispatch friendly.
// Mouse look matches playground mousePosition / ShaderToy iMouse (pixel coords).
// © shader-slang / afl_ext — adapted.

module sp03_ocean;

import slangpy;

static const float DRAG_MULT = 0.38f;
static const float WATER_DEPTH = 1.0f;
static const float CAMERA_HEIGHT = 1.5f;
static const int ITERATIONS_RAYMARCH = 12;
static const int ITERATIONS_NORMAL = 24;
static const int AA = 3; // 3x3 supersample (smoother horizon at 640; still FPS-friendly)

[Differentiable]
[PreferCheckpoint]
float2 wavedx(float2 position, float2 direction, float frequency, float timeshift)
{
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0f);
    float dx = wave * cos(x);
    return float2(wave, -dx);
}

[Differentiable]
float getwaves(float2 position, float time, int iterations)
{
    float wavePhaseShift = length(position) * 0.1f;
    float iter = 0.0f;
    float frequency = 1.0f;
    float timeMultiplier = 5.0f;
    float weight = 1.0f;
    float sumOfValues = 0.0f;
    float sumOfWeights = 0.0f;
    [MaxIters(64)]
    for (int i = 0; i < iterations; i++)
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

float raymarchwater(float3 camera, float3 start, float3 end, float depth, float time)
{
    float3 pos = start;
    float3 dir = normalize(end - start);
    for (int i = 0; i < 48; i++)
    {
        float height = getwaves(pos.xz, time, ITERATIONS_RAYMARCH) * depth - depth;
        if (height + 0.01f > pos.y)
            return distance(pos, camera);
        pos += dir * (pos.y - height);
    }
    return distance(start, camera);
}

float3 wave_normal(float2 pos, float depth, float time)
{
    float e = 0.01f;
    float h = getwaves(pos, time, ITERATIONS_NORMAL);
    float hx = getwaves(pos + float2(e, 0.0f), time, ITERATIONS_NORMAL);
    float hz = getwaves(pos + float2(0.0f, e), time, ITERATIONS_NORMAL);
    return normalize(float3(-(hx - h) / e, 1.0f, -(hz - h) / e));
}

float3x3 createRotationMatrixAxisAngle(float3 axis, float angle)
{
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0f - c;
    return float3x3(
        oc * axis.x * axis.x + c,
        oc * axis.x * axis.y - axis.z * s,
        oc * axis.z * axis.x + axis.y * s,
        oc * axis.x * axis.y + axis.z * s,
        oc * axis.y * axis.y + c,
        oc * axis.y * axis.z + axis.x * s,
        oc * axis.z * axis.x - axis.y * s,
        oc * axis.y * axis.z + axis.x * s,
        oc * axis.z * axis.z + c);
}

/// Camera ray from fragCoord + mouse (playground mousePosition / ShaderToy iMouse).
/// ``mouse`` is pixel coords, top-left origin; (0,0) keeps a default pitch.
float3 getRay(float2 fragCoord, float2 resolution, float2 mouse)
{
    float2 uv = ((fragCoord / resolution) * 2.0f - 1.0f)
                * float2(resolution.x / resolution.y, 1.0f);
    float3 proj = normalize(float3(uv.x, uv.y, 1.5f));
    float2 nm = mouse / resolution;
    float mx = nm.x;
    float my = (nm.y == 0.0f) ? 0.35f : nm.y;
    float yaw = 3.0f * ((1.0f - mx + 0.5f) * 2.0f - 1.0f);
    float pitchA = 0.5f + 1.5f * ((my * 1.0f) * 2.0f - 1.0f);
    float3x3 mat = createRotationMatrixAxisAngle(float3(0.0f, -1.0f, 0.0f), yaw);
    float3x3 pitch = createRotationMatrixAxisAngle(float3(1.0f, 0.0f, 0.0f), pitchA);
    return mul(mat, mul(pitch, proj));
}

float intersectPlane(float3 origin, float3 direction, float3 point, float3 normal)
{
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0f, 9991999.0f);
}

float3 extra_cheap_atmosphere(float3 raydir, float3 sundir)
{
    sundir.y = max(sundir.y, -0.07f);
    float special_trick = 1.0f / (raydir.y * 1.0f + 0.1f);
    float special_trick2 = 1.0f / (sundir.y * 11.0f + 1.0f);
    float raysundt = pow(abs(dot(sundir, raydir)), 2.0f);
    float sundt = pow(max(0.0f, dot(sundir, raydir)), 8.0f);
    float mymie = sundt * special_trick * 0.2f;
    float3 suncolor =
        lerp(float3(1.0f, 1.0f, 1.0f),
             max(float3(0.0f, 0.0f, 0.0f), float3(1.0f, 1.0f, 1.0f) - float3(5.5f, 13.0f, 22.4f) / 22.4f),
             special_trick2);
    float3 bluesky = float3(5.5f, 13.0f, 22.4f) / 22.4f * suncolor;
    float3 bluesky2 =
        max(float3(0.0f, 0.0f, 0.0f),
            bluesky - float3(5.5f, 13.0f, 22.4f) * 0.002f
                * (special_trick + -6.0f * sundir.y * sundir.y));
    bluesky2 *= special_trick * (0.24f + raysundt * 0.24f);
    return bluesky2 * (1.0f + 1.0f * pow(1.0f - raydir.y, 3.0f)) + float3(mymie, mymie, mymie);
}

float3 getSunDirection(float time)
{
    return normalize(float3(sin(time), 1.0f, cos(time)));
}

float3 getAtmosphere(float3 dir, float time)
{
    return extra_cheap_atmosphere(dir, getSunDirection(time)) * 0.5f;
}

float getSun(float3 dir, float time)
{
    return pow(max(0.0f, dot(dir, getSunDirection(time))), 720.0f) * 210.0f;
}

float3 aces_tonemap(float3 color)
{
    float3x3 m1 = float3x3(
        0.59719f, 0.07600f, 0.02840f, 0.35458f, 0.90834f, 0.13383f, 0.04823f, 0.01566f, 0.83777f);
    float3x3 m2 = float3x3(
        1.60475f, -0.10208f, -0.00327f, -0.53108f, 1.10813f, -0.07276f, -0.07367f, -0.00605f,
        1.07602f);
    float3 v = mul(color, m1);
    float3 a = v * (v + 0.0245786f) - 0.000090537f;
    float3 b = v * (0.983729f * v + 0.4329510f) + 0.238081f;
    return pow(clamp(mul((a / b), m2), 0.0f, 1.0f), float3(1.0f / 2.2f, 1.0f / 2.2f, 1.0f / 2.2f));
}

float3 render_ocean(float2 frag, float2 size, float time, float2 mouse)
{
    float3 ray = getRay(frag, size, mouse);
    if (ray.y >= 0.0f)
    {
        float3 C = getAtmosphere(ray, time) + getSun(ray, time);
        return aces_tonemap(C * 2.0f);
    }

    float3 waterPlaneHigh = float3(0.0f, 0.0f, 0.0f);
    float3 waterPlaneLow = float3(0.0f, -WATER_DEPTH, 0.0f);
    float3 origin = float3(time * 2.0f, CAMERA_HEIGHT, 1.0f);

    float highPlaneHit =
        intersectPlane(origin, ray, waterPlaneHigh, float3(0.0f, 1.0f, 0.0f));
    float lowPlaneHit = intersectPlane(origin, ray, waterPlaneLow, float3(0.0f, 1.0f, 0.0f));
    float3 highHitPos = origin + ray * highPlaneHit;
    float3 lowHitPos = origin + ray * lowPlaneHit;

    float dist = raymarchwater(origin, highHitPos, lowHitPos, WATER_DEPTH, time);
    float3 waterHitPos = origin + ray * dist;
    float3 N = wave_normal(waterHitPos.xz, WATER_DEPTH, time);
    float interpFactor = 0.8f * min(1.0f, sqrt(dist * 0.01f) * 1.1f);
    N = lerp(N, float3(0.0f, 1.0f, 0.0f), interpFactor);

    float fresnel = (0.04f + (1.0f - 0.04f) * (pow(1.0f - max(0.0f, dot(-N, ray)), 5.0f)));
    float3 R = normalize(reflect(ray, N));
    R.y = abs(R.y);

    float3 reflection = getAtmosphere(R, time) + getSun(R, time);
    float3 scattering = float3(0.0293f, 0.0698f, 0.1717f) * 0.1f
                        * (0.2f + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);
    float3 C = fresnel * reflection + scattering;
    return aces_tonemap(C * 2.0f);
}

/// ``mouse``: pixel coords (top-left), ShaderToy-style; drag in live preview to look.
public float3 hello_pixel(int2 pixel, int2 resolution, float time, float2 mouse)
{
    float2 size = float2(resolution);
    // ShaderToy NDC is Y+ up; our pixel (0,0) is top-left — flip Y for sky/water.
    float2 base = float2(float(pixel.x), float(resolution.y - 1 - pixel.y));
    float3 acc = float3(0.0f, 0.0f, 0.0f);
    for (int j = 0; j < AA; j++)
    {
        for (int i = 0; i < AA; i++)
        {
            float2 off = float2(
                (float(i) + 0.5f) / float(AA),
                (float(j) + 0.5f) / float(AA));
            // Flip Y offset with the same top-left → bottom-up convention.
            float2 frag = base + float2(off.x, 1.0f - off.y);
            acc += render_ocean(frag, size, time, mouse);
        }
    }
    return acc / float(AA * AA);
}

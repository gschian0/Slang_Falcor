// Boid impostor raster — SV_VertexID quads facing camera. No Scene.Raster / alphaTest.

struct Boid
{
    float3 pos;
    float pad0;
    float3 vel;
    float pad1;
};

StructuredBuffer<Boid> gBoids;

cbuffer PerFrameCB
{
    float4x4 gViewProj;
    float3 gCamPos;
    float gSize;
    float3 gCamRight;
    float gTime;
    float3 gCamUp;
    uint gCount;
};

struct VsOut
{
    float4 posH : SV_POSITION;
    float2 uv : TEXCOORD0;
    float speed : TEXCOORD1;
};

VsOut vsMain(uint vid : SV_VertexID)
{
    VsOut o;
    uint boidId = vid / 6;
    uint corner = vid % 6;
    // two triangles: 0,1,2 and 0,2,3
    uint c = corner < 3 ? corner : (corner == 3 ? 0 : (corner == 4 ? 2 : 3));
    float2 q = float2((c == 1 || c == 2) ? 1.f : -1.f, (c >= 2) ? 1.f : -1.f);

    Boid b = gBoids[min(boidId, gCount - 1)];
    float3 right = gCamRight;
    float3 up = gCamUp;
    float3 posW = b.pos + (right * q.x + up * q.y) * gSize;
    o.posH = mul(gViewProj, float4(posW, 1.f));
    o.uv = q * 0.5f + 0.5f;
    o.speed = length(b.vel);
    return o;
}

float4 psMain(VsOut i) : SV_TARGET
{
    float2 p = i.uv * 2.f - 1.f;
    float r = length(p);
    if (r > 1.f)
        discard;
    float core = saturate(1.f - r);
    float rim = smoothstep(0.55f, 1.f, r);
    float3 body = lerp(float3(0.95f, 0.82f, 0.35f), float3(0.25f, 0.55f, 0.95f), saturate(i.speed * 0.22f));
    float3 col = body * (0.45f + 0.55f * core) + float3(0.9f, 0.95f, 1.f) * rim * 0.35f;
    return float4(col, 1.f);
}

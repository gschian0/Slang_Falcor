// Classic Reynolds boids — compute school file (separation / alignment / cohesion).
// Dispatch each frame; raster impostors read the same structured buffer. No Scene.Raster.
// Iteration 8: host sliders drive weights / speed / neighbor scale. Count is gCount (buffer is max-sized).

struct Boid
{
    float3 pos;
    float pad0;
    float3 vel;
    float pad1;
};

StructuredBuffer<Boid> gIn;
RWStructuredBuffer<Boid> gOut;

cbuffer PerFrameCB
{
    uint gCount;
    float gDt;
    float gTime;
    float gPad;
    float3 gOrigin;
    float gRadius;
    float gSepW;
    float gAliW;
    float gCohW;
    float gMaxSpeed;
    float gNeighborR;
    float gPad1;
    float gPad2;
    float gPad3;
};

[shader("compute")]
[numthreads(64, 1, 1)]
void main(uint3 tid : SV_DispatchThreadID)
{
    uint i = tid.x;
    if (i >= gCount)
        return;

    Boid me = gIn[i];
    float3 sep = float3(0, 0, 0);
    float3 ali = float3(0, 0, 0);
    float3 coh = float3(0, 0, 0);
    uint nAli = 0;
    uint nCoh = 0;

    float nr = max(gNeighborR, 0.15f);
    const float sepDist = 0.85f * nr;
    const float aliDist = 2.4f * nr;
    const float cohDist = 3.6f * nr;

    for (uint j = 0; j < gCount; j++)
    {
        if (j == i)
            continue;
        Boid other = gIn[j];
        float3 d = me.pos - other.pos;
        float dist = length(d);
        if (dist < 1e-4f)
            continue;
        if (dist < sepDist)
            sep += d / (dist * dist);
        if (dist < aliDist)
        {
            ali += other.vel;
            nAli++;
        }
        if (dist < cohDist)
        {
            coh += other.pos;
            nCoh++;
        }
    }

    float3 acc = float3(0, 0, 0);
    acc += sep * gSepW;
    if (nAli > 0)
        acc += (ali / float(nAli) - me.vel) * gAliW;
    if (nCoh > 0)
        acc += ((coh / float(nCoh)) - me.pos) * gCohW;

    // Soft keep-in: flock over ocean / sky around gOrigin, not on canvases.
    float3 toC = gOrigin - me.pos;
    float r = length(toC);
    if (r > gRadius)
        acc += normalize(toC) * (r - gRadius) * 0.35f;
    acc.y += (gOrigin.y - me.pos.y) * 0.04f;

    float dt = saturate(gDt) * 1.6f + 0.008f;
    me.vel += acc * dt;
    float spd = length(me.vel);
    float maxSpd = gMaxSpeed + 0.6f * sin(gTime * 0.35f + float(i) * 0.05f);
    if (spd > maxSpd)
        me.vel *= maxSpd / spd;
    if (spd < 0.35f)
        me.vel = (spd > 1e-4f) ? me.vel * (0.55f / spd) : float3(0.4f, 0.05f, 0.2f);

    me.pos += me.vel * dt;
    me.pos.y = max(me.pos.y, 1.35f);
    gOut[i] = me;
}

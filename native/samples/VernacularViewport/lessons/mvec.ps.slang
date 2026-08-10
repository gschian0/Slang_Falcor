// Reconstruct screen-space UV motion from depth + prev/current view-proj.
// School: TAA / DLSS want mvec; research apps get them from the G-buffer, not a hamster wheel.

cbuffer PerFrameCB
{
    float4x4 gInvViewProj;
    float4x4 gPrevViewProj;
};

Texture2D gDepth;
SamplerState gSampler;

float4 main(float2 texC : TEXCOORD) : SV_TARGET0
{
    float depth = gDepth.SampleLevel(gSampler, texC, 0).r;
    // D3D NDC: x left→right, y bottom→top. Falcor blit TEXCOORD is top-left UV.
    float2 ndc = float2(texC.x * 2.f - 1.f, 1.f - texC.y * 2.f);
    float4 clip = float4(ndc, depth, 1.f);
    float4 world = mul(gInvViewProj, clip);
    world /= max(world.w, 1e-6f);

    float4 prevH = mul(gPrevViewProj, float4(world.xyz, 1.f));
    float2 prevNdc = prevH.xy / max(prevH.w, 1e-6f);
    float2 prevUv = float2(prevNdc.x * 0.5f + 0.5f, 0.5f - prevNdc.y * 0.5f);
    float2 motion = prevUv - texC;
    return float4(motion, 0.f, 1.f);
}

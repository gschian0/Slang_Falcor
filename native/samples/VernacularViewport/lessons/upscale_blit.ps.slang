// Internal-res → swapchain blit. Linear or Catmull-Rom bicubic (school cheap upscale).

cbuffer PerFrameCB
{
    uint gBicubic;
    float3 gPad;
};

Texture2D gSrc;
SamplerState gSampler;

float3 bicubicSampleCatmullRom(Texture2D tex, SamplerState samp, float2 uv, float2 texDim)
{
    float2 samplePos = uv * texDim;
    float2 invTextureSize = 1.0 / texDim;
    float2 tc = floor(samplePos - 0.5f) + 0.5f;
    float2 f = samplePos - tc;
    float2 f2 = f * f;
    float2 f3 = f2 * f;

    float2 w0 = f2 - 0.5f * (f3 + f);
    float2 w1 = 1.5f * f3 - 2.5f * f2 + 1.f;
    float2 w3 = 0.5f * (f3 - f2);
    float2 w2 = 1 - w0 - w1 - w3;
    float2 w12 = w1 + w2;

    float2 tc0 = (tc - 1.f) * invTextureSize;
    float2 tc12 = (tc + w2 / w12) * invTextureSize;
    float2 tc3 = (tc + 2.f) * invTextureSize;

    return tex.SampleLevel(samp, float2(tc0.x, tc0.y), 0.f).rgb * (w0.x * w0.y) +
           tex.SampleLevel(samp, float2(tc0.x, tc12.y), 0.f).rgb * (w0.x * w12.y) +
           tex.SampleLevel(samp, float2(tc0.x, tc3.y), 0.f).rgb * (w0.x * w3.y) +
           tex.SampleLevel(samp, float2(tc12.x, tc0.y), 0.f).rgb * (w12.x * w0.y) +
           tex.SampleLevel(samp, float2(tc12.x, tc12.y), 0.f).rgb * (w12.x * w12.y) +
           tex.SampleLevel(samp, float2(tc12.x, tc3.y), 0.f).rgb * (w12.x * w3.y) +
           tex.SampleLevel(samp, float2(tc3.x, tc0.y), 0.f).rgb * (w3.x * w0.y) +
           tex.SampleLevel(samp, float2(tc3.x, tc12.y), 0.f).rgb * (w3.x * w12.y) +
           tex.SampleLevel(samp, float2(tc3.x, tc3.y), 0.f).rgb * (w3.x * w3.y);
}

float4 main(float2 texC : TEXCOORD) : SV_TARGET0
{
    uint2 texDim;
    uint levels;
    gSrc.GetDimensions(0, texDim.x, texDim.y, levels);
    float3 c = (gBicubic != 0)
                   ? bicubicSampleCatmullRom(gSrc, gSampler, texC, float2(texDim))
                   : gSrc.SampleLevel(gSampler, texC, 0).rgb;
    return float4(c, 1.f);
}

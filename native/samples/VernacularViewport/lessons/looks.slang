// VERNACULAR cube lesson looks — superseded by shading_ladder.slang (temple + vibration).
// Kept so sync still copies lessons/. Temple env lives in temple_env.slang.

float3 shadeCubeLook(float2 uv, float3 N, float3 V, float3 posW)
{
    return float3(uv, 0.25f) * (0.5f + 0.5f * saturate(dot(normalize(N), V)));
}

// Temple / Vibration pixel — school file (looks + lighting modes + env).
// Pixel = chapter bank + L lighting + ocean/sky/land. Analytic only (no alphaTest).

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

    // Hero canvases — plane / sphere / cube share LessonCanvas look.
    // World-scale UVs: 1 look unit ≈ 1 world meter (no 0–1 stretch on resize).
    float2 lookUv = worldScaleUv(posW, N);
    float3 albedo = float3(0.72f, 0.55f, 0.48f);
    uint mid = triangleIndex % 3;
    if (mid == 1)
        albedo = float3(0.35f, 0.4f, 0.55f);
    else if (mid == 2)
        albedo = float3(0.55f, 0.45f, 0.75f);
    float3 look = shadeChapterLook(lookUv, N, view, posW, albedo);
    look = applyLightMode(look, N, view);
    // Soft temple rim so canvases float in haze
    float rim = pow(1.f - saturate(abs(dot(N, view))), 2.6f);
    look += float3(0.35f, 0.55f, 0.95f) * rim * 0.35f;
    look = applyFog(look * 1.4f, posW, cam, ray);
    return float4(aces_tonemap(look), 1.f);
}

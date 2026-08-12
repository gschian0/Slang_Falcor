// Temple / Vibration vertex — school file (edit in F8 in-app editor, Ctrl+S / F5 reload).
// Vertex = placement + vibration. Ocean deck is flattened here; beauty is raymarched in PS.

VSOut vsMain(VSIn vIn)
{
    VSOut vOut = defaultVS(vIn);

    if (gShowMode == 1)
    {
        if (vOut.materialID == gMatFloor)
            return vOut;
        if (gVertexWaves != 0 && gVibeAmp > 1e-4f)
        {
            int2 modeIgnored;
            float w = vibrationMode(vOut.posW, gTime, modeIgnored);
            float env = (gChapter == 9) ? pow(abs(sin(gTime * 1.7f)), 0.35f) : 1.f;
            float3 n = normalize(vOut.normalW);
            float3 disp = float3(0.f, 1.f, 0.f) * (w * gVibeAmp * env);
            disp += n * (w * gVibeAmp * 0.35f * env);
            float localRipple = 0.15f * sin(12.f * vIn.pos.x + gTime * 4.f) * sin(12.f * vIn.pos.z + gTime * 3.1f);
            disp.y += localRipple * gVibeAmp * env;
            vOut.posW += disp;
            vOut.posH = mul(gScene.camera.getViewProj(), float4(vOut.posW, 1.f));
        }
        return vOut;
    }

    // Temple — flatten ocean grid to water deck (raymarch beauty in PS)
    if (vOut.materialID == gMatOcean)
    {
        vOut.posW.y = min(vOut.posW.y, 0.f);
        vOut.normalW = float3(0.f, 1.f, 0.f);
        vOut.posH = mul(gScene.camera.getViewProj(), float4(vOut.posW, 1.f));
    }
    return vOut;
}

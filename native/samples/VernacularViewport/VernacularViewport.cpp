// VERNACULAR — Temple of Secret Knowledge + pinned Vibration Modes (analytic raster).
#include "VernacularViewport.h"

#include "Scene/SceneBuilder.h"
#include "Scene/TriangleMesh.h"
#include "Scene/Material/StandardMaterial.h"
#include "Scene/Lights/Light.h"
#include "Scene/Camera/Camera.h"
#include "Scene/Transform.h"
#include "Utils/UI/TextRenderer.h"
#include "Core/API/RasterizerState.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

#if FALCOR_WINDOWS
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <functiondiscoverykeys_devpkey.h>
#pragma comment(lib, "ole32.lib")
#endif

FALCOR_EXPORT_D3D12_AGILITY_SDK

namespace
{
const float4 kClearTemple(0.04f, 0.05f, 0.09f, 1.f);
const float4 kClearVibe(0.05f, 0.06f, 0.09f, 1.f);

// Falcor MouseEvent::pos is normalized [0,1]. Gains are radians per full-width/height drag.
// Iteration 2 used ~0.004 (pixel-scale) which made orbit feel dead after Temple landed.
constexpr float kLookGain = 2.8f;
constexpr float kWheelZoom = 0.9f;

std::string asciiForHud(const std::string& s)
{
    std::string out;
    out.reserve(s.size());
    for (unsigned char c : s)
    {
        if (c >= 32 && c <= 126)
            out.push_back(static_cast<char>(c));
        else if (c == '\n' || c == '\r' || c == '\t')
            out.push_back(' ');
    }
    return out;
}

struct Glyph
{
    char ch;
    uint8_t rows[7];
};

// clang-format off
const Glyph kGlyphs[] = {
    {'A', {0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001}},
    {'B', {0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110}},
    {'C', {0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110}},
    {'D', {0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110}},
    {'E', {0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111}},
    {'F', {0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000}},
    {'G', {0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110}},
    {'H', {0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001}},
    {'I', {0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110}},
    {'M', {0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001, 0b10001}},
    {'N', {0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001}},
    {'O', {0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110}},
    {'R', {0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001}},
    {'S', {0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110}},
    {'T', {0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100}},
    {'U', {0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110}},
    {'V', {0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100}},
    {' ', {0, 0, 0, 0, 0, 0, 0}},
};
// clang-format on

const Glyph* findGlyph(char c)
{
    c = (char)std::toupper((unsigned char)c);
    for (const Glyph& g : kGlyphs)
        if (g.ch == c)
            return &g;
    return nullptr;
}

const VernacularViewport::ChapterStation kStations[16] = {
    {"Ch0 Hello UV", "monkey",
     "See the surface — UV coordinates. Temple canvases share one look.",
     "Delta-wave tone on this chapter (M mute). [ ] banks the ladder."},
    {"Ch1 World normals", "monkey",
     "See orientation — normals remapped so faces read in space.",
     "Orbit: same geometry, new look."},
    {"Ch2 Lambert", "ape",
     "Classic shading property: diffuse clay (N·L).",
     "Named property — not magic. Compare to Blinn next."},
    {"Ch3 Blinn-Phong", "ape",
     "Classic shading property: specular lobe (N·H^n).",
     "Diffuse + highlight — what Physical will compose next."},
    {"Ch4 Physical", "space monkey",
     "Full / physical shading — built from those properties.",
     "Same canvases. Classics were approximating this."},
    {"Ch5 Splatter paint", "paint",
     "Gaussian blobs on UV — paint before lighting.",
     "Later lit variants bring Lambert back."},
    {"Ch6 Soft brush", "paint",
     "Animated brush trail across the face.",
     "Temple haze still wraps the rim."},
    {"Ch7 Potluck hash", "paint",
     "Hash palette cells — bring what you got.",
     "Lambert wraps the hash colors."},
    {"Ch8 Neural tiny-net", "paint",
     "Tiny 3→8→3 net on UV + time.",
     "Inference in-shader — sister to 2D neural labs."},
    {"Ch9 Jack-in-box vibe", "paint",
     "Sharp envelope + mode field (best on Vibration show).",
     "F3 switches to Vibration Modes lattices."},
    {"Ch10 Splatter lit", "paint",
     "Splatter × Lambert — paint meets classic diffuse.",
     "Compare to Ch5 unlit splatter."},
    {"Ch11 Neural lit", "paint",
     "Neural × Blinn — network albedo with specular.",
     "Compare to Ch8 unlit neural."},
    {"Ch12 Potluck neon", "paint",
     "Potluck hash mixed with soft brush neon.",
     "End of ladder pack — school ports continue."},
    {"Ch13 Circle (sp02)", "school",
     "Slang Playground circle / beam spirit on the canvas.",
     "2D sister: slang_playground/sp02_circle"},
    {"Ch14 Shaping (BoS)", "school",
     "Book of Shaders shaping — y = pow(x,3) plot line.",
     "2D sister: bos/02_shaping"},
    {"Ch15 Patterns (BoS)", "school",
     "Book of Shaders tiled soft circles.",
     "2D sister: bos/05_patterns"},
};

ref<TriangleMesh> createOceanGrid(int segs, float size)
{
    auto mesh = TriangleMesh::create();
    float half = size * 0.5f;
    for (int y = 0; y <= segs; ++y)
    {
        for (int x = 0; x <= segs; ++x)
        {
            float u = float(x) / float(segs);
            float v = float(y) / float(segs);
            float3 p = float3(-half + size * u, -half + size * v, 0.f);
            mesh->addVertex(p, float3(0, 0, 1), float2(u, v));
        }
    }
    for (int y = 0; y < segs; ++y)
    {
        for (int x = 0; x < segs; ++x)
        {
            uint32_t i0 = y * (segs + 1) + x;
            uint32_t i1 = i0 + 1;
            uint32_t i2 = i0 + (segs + 1);
            uint32_t i3 = i2 + 1;
            mesh->addTriangle(i0, i2, i1);
            mesh->addTriangle(i1, i2, i3);
        }
    }
    return mesh;
}

#if FALCOR_WINDOWS
// Two close sines → ~2 Hz beat (delta-wave range). Graphics never waits on this.
void audioThreadMain(std::atomic<bool>* run, std::atomic<bool>* active, std::string* status)
{
    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    const bool comOk = SUCCEEDED(hr) || hr == RPC_E_CHANGED_MODE;
    if (!comOk)
    {
        *status = "audio: COM init failed";
        return;
    }

    IMMDeviceEnumerator* pEnum = nullptr;
    hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), nullptr, CLSCTX_ALL, __uuidof(IMMDeviceEnumerator), (void**)&pEnum);
    if (FAILED(hr) || !pEnum)
    {
        *status = "audio: no enumerator";
        if (comOk && hr != RPC_E_CHANGED_MODE)
            CoUninitialize();
        return;
    }

    IMMDevice* pDevice = nullptr;
    hr = pEnum->GetDefaultAudioEndpoint(eRender, eConsole, &pDevice);
    pEnum->Release();
    if (FAILED(hr) || !pDevice)
    {
        *status = "audio: no endpoint";
        if (SUCCEEDED(hr) == false && comOk)
            CoUninitialize();
        return;
    }

    IAudioClient* pClient = nullptr;
    hr = pDevice->Activate(__uuidof(IAudioClient), CLSCTX_ALL, nullptr, (void**)&pClient);
    pDevice->Release();
    if (FAILED(hr) || !pClient)
    {
        *status = "audio: activate failed";
        CoUninitialize();
        return;
    }

    WAVEFORMATEX* pWfx = nullptr;
    hr = pClient->GetMixFormat(&pWfx);
    if (FAILED(hr) || !pWfx)
    {
        *status = "audio: mix format failed";
        pClient->Release();
        CoUninitialize();
        return;
    }

    const REFERENCE_TIME bufferDuration = 10000000; // 1s
    hr = pClient->Initialize(AUDCLNT_SHAREMODE_SHARED, 0, bufferDuration, 0, pWfx, nullptr);
    if (FAILED(hr))
    {
        *status = "audio: init failed";
        CoTaskMemFree(pWfx);
        pClient->Release();
        CoUninitialize();
        return;
    }

    UINT32 bufferFrames = 0;
    pClient->GetBufferSize(&bufferFrames);
    IAudioRenderClient* pRender = nullptr;
    hr = pClient->GetService(__uuidof(IAudioRenderClient), (void**)&pRender);
    if (FAILED(hr) || !pRender)
    {
        *status = "audio: render client failed";
        CoTaskMemFree(pWfx);
        pClient->Release();
        CoUninitialize();
        return;
    }

    pClient->Start();
    *status = "audio: WASAPI delta OK";

    const double sampleRate = pWfx->nSamplesPerSec > 0 ? double(pWfx->nSamplesPerSec) : 48000.0;
    const int channels = std::max(1, int(pWfx->nChannels));
    // Shared mix format is typically float32 (WAVE_FORMAT_EXTENSIBLE); fall back to silence otherwise.
    const bool isFloat = (pWfx->wBitsPerSample == 32);
    double phaseA = 0.0, phaseB = 0.0;
    const double freqA = 120.0;
    const double freqB = 122.0; // ~2 Hz beat
    const double twoPi = 6.283185307179586;

    while (run->load())
    {
        UINT32 padding = 0;
        pClient->GetCurrentPadding(&padding);
        UINT32 available = bufferFrames - padding;
        if (available < 256)
        {
            Sleep(5);
            continue;
        }

        BYTE* pData = nullptr;
        if (FAILED(pRender->GetBuffer(available, &pData)) || !pData)
        {
            Sleep(5);
            continue;
        }

        const bool tone = active->load();
        if (isFloat)
        {
            float* samples = reinterpret_cast<float*>(pData);
            for (UINT32 i = 0; i < available; ++i)
            {
                float s = 0.f;
                if (tone)
                {
                    s = 0.08f * float(std::sin(phaseA) + std::sin(phaseB));
                    phaseA += twoPi * freqA / sampleRate;
                    phaseB += twoPi * freqB / sampleRate;
                    if (phaseA > twoPi)
                        phaseA -= twoPi;
                    if (phaseB > twoPi)
                        phaseB -= twoPi;
                }
                for (int c = 0; c < channels; ++c)
                    samples[i * channels + c] = s;
            }
        }
        else
        {
            // Silence / zero if not float mix — still don't crash
            std::memset(pData, 0, size_t(available) * pWfx->nBlockAlign);
        }

        pRender->ReleaseBuffer(available, tone ? 0 : AUDCLNT_BUFFERFLAGS_SILENT);
        Sleep(8);
    }

    pClient->Stop();
    pRender->Release();
    CoTaskMemFree(pWfx);
    pClient->Release();
    CoUninitialize();
    *status = "audio: stopped";
}
#endif
} // namespace

VernacularViewport::VernacularViewport(const SampleAppConfig& config) : SampleApp(config) {}

VernacularViewport::~VernacularViewport()
{
    shutdownAudio();
}

const VernacularViewport::ChapterStation& VernacularViewport::activeStation() const
{
    return kStations[mChapter % kChapterCount];
}

const char* VernacularViewport::chapterName() const
{
    return activeStation().title;
}

const char* VernacularViewport::moveModeName() const
{
    return (mMoveMode == MoveMode::Orbit) ? "Orbit" : "Fly";
}

void VernacularViewport::clearFlyKeys()
{
    mKeyW = mKeyA = mKeyS = mKeyD = mKeyQ = mKeyE = false;
    mKeyShift = false;
    mLookDrag = false;
}

float3 VernacularViewport::lookDirFromYawPitch() const
{
    float cp = std::cos(mCamPitch), sp = std::sin(mCamPitch);
    float cy = std::cos(mCamYaw), sy = std::sin(mCamYaw);
    // Opposite of orbit "back" vector — look toward the target / into the scene.
    return normalize(float3(-sy * cp, -sp, -cy * cp));
}

void VernacularViewport::syncOrbitFromEye()
{
    float3 toEye = mFlyPos - mOrbitTarget;
    float dist = length(toEye);
    if (dist < 1e-3f)
        return;
    mCamDist = dist;
    float3 back = toEye / dist;
    mCamPitch = std::clamp(std::asin(std::clamp(back.y, -1.f, 1.f)), -1.2f, 1.35f);
    mCamYaw = std::atan2(back.x, back.z);
}

void VernacularViewport::setMoveMode(MoveMode mode)
{
    if (mMoveMode == mode)
        return;

    if (mode == MoveMode::Orbit)
    {
        // Keep the current eye; re-aim orbit at the look hit along view (or keep target).
        float3 forward = lookDirFromYawPitch();
        mOrbitTarget = mFlyPos + forward * std::max(4.f, mCamDist * 0.65f);
        syncOrbitFromEye();
        clearFlyKeys();
        mStatusMsg = "Movement: Orbit (RMB drag, wheel zoom)";
    }
    else
    {
        // Enter fly from current orbit eye / look.
        float cp = std::cos(mCamPitch), sp = std::sin(mCamPitch);
        float cy = std::cos(mCamYaw), sy = std::sin(mCamYaw);
        float3 back = float3(sy * cp, sp, cy * cp);
        mFlyPos = mOrbitTarget + back * mCamDist;
        clearFlyKeys();
        mStatusMsg = "Movement: Fly (WASD QE, RMB look, Shift faster)";
    }
    mMoveMode = mode;
}

void VernacularViewport::addCubeInstance(SceneBuilder& builder, MeshID meshID, const float3& pos, float scale, const std::string& name)
{
    Transform xform;
    xform.setTranslation(pos);
    xform.setScaling(float3(scale));
    NodeID node = builder.addNode(SceneBuilder::Node{name, xform.getMatrix(), float4x4(), float4x4()});
    builder.addMeshInstance(node, meshID);
}

void VernacularViewport::initAudio()
{
#if FALCOR_WINDOWS
    if (mAudioRun.load())
        return;
    mAudioRun = true;
    mAudioActive = false;
    mAudioThread = std::thread(
        audioThreadMain, &mAudioRun, &mAudioActive, &mAudioStatus
    );
    mAudioOk = true;
#else
    mAudioOk = false;
    mAudioStatus = "audio: Windows-only stub";
#endif
}

void VernacularViewport::shutdownAudio()
{
    mAudioActive = false;
    mAudioRun = false;
    if (mAudioThread.joinable())
        mAudioThread.join();
    mAudioOk = false;
}

void VernacularViewport::updateAudioState()
{
    const bool want = (mShowMode == ShowMode::TempleSchool) && (mChapter == 0) && !mAudioMute && mAudioOk;
    mAudioActive = want;
}

void VernacularViewport::onLoad(RenderContext* /*pRenderContext*/)
{
    initAudio();
    buildVernacularScene(getTargetFbo().get());
    mLastFrameTime = getGlobalClock().getTime();
}

void VernacularViewport::onResize(uint32_t width, uint32_t height)
{
    if (mpCamera && height > 0)
        mpCamera->setAspectRatio(float(width) / float(height));
}

void VernacularViewport::switchShowMode(ShowMode mode)
{
    if (mShowMode == mode)
        return;
    mShowMode = mode;
    buildVernacularScene(getTargetFbo().get());
    mStatusMsg = (mode == ShowMode::TempleSchool) ? "Show: Temple School" : "Show: Vibration Modes (pinned)";
    updateAudioState();
}

void VernacularViewport::buildTempleScene(SceneBuilder& builder, const Fbo* pTargetFbo)
{
    auto pMatSky = StandardMaterial::create(getDevice(), "Sky");
    pMatSky->setBaseColor(float4(0.35f, 0.45f, 0.85f, 1.f));
    pMatSky->setDoubleSided(true);

    auto pMatOcean = StandardMaterial::create(getDevice(), "Ocean");
    pMatOcean->setBaseColor(float4(0.04f, 0.12f, 0.22f, 1.f));
    pMatOcean->setRoughness(0.12f);
    pMatOcean->setDoubleSided(true);

    auto pMatLand = StandardMaterial::create(getDevice(), "Land");
    pMatLand->setBaseColor(float4(0.3f, 0.32f, 0.4f, 1.f));
    pMatLand->setRoughness(0.9f);
    pMatLand->setDoubleSided(true);

    auto pMatCanvas = StandardMaterial::create(getDevice(), "LessonCanvas");
    pMatCanvas->setBaseColor(float4(0.75f, 0.55f, 0.45f, 1.f));
    pMatCanvas->setRoughness(0.4f);
    pMatCanvas->setMetallic(0.1f);
    pMatCanvas->setDoubleSided(true);

    MeshID skyID = builder.addTriangleMesh(TriangleMesh::createSphere(90.f, 48, 24), pMatSky);
    MeshID oceanID = builder.addTriangleMesh(createOceanGrid(80, 140.f), pMatOcean);
    MeshID landFlatID = builder.addTriangleMesh(TriangleMesh::createQuad(float2(1.f)), pMatLand);
    MeshID landHillID = builder.addTriangleMesh(TriangleMesh::createCube(float3(1.f)), pMatLand);
    MeshID planeID = builder.addTriangleMesh(TriangleMesh::createQuad(float2(1.f)), pMatCanvas);
    MeshID sphereID = builder.addTriangleMesh(TriangleMesh::createSphere(0.85f, 32, 16), pMatCanvas);
    MeshID cubeID = builder.addTriangleMesh(TriangleMesh::createCube(float3(1.f)), pMatCanvas);

    Transform skyX;
    skyX.setTranslation(float3(0.f));
    builder.addMeshInstance(builder.addNode(SceneBuilder::Node{"SkyDome", skyX.getMatrix(), float4x4(), float4x4()}), skyID);

    Transform oceanX;
    oceanX.setTranslation(float3(0.f, 0.f, 0.f));
    oceanX.setRotationEulerDeg(float3(-90.f, 0.f, 0.f));
    builder.addMeshInstance(builder.addNode(SceneBuilder::Node{"Ocean", oceanX.getMatrix(), float4x4(), float4x4()}), oceanID);

    auto addLandFlat = [&](const char* name, float3 pos, float2 scaleXZ, float yawDeg = 0.f)
    {
        Transform t;
        t.setTranslation(pos);
        t.setRotationEulerDeg(float3(-90.f, yawDeg, 0.f));
        t.setScaling(float3(scaleXZ.x, scaleXZ.y, 1.f));
        NodeID n = builder.addNode(SceneBuilder::Node{name, t.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, landFlatID);
    };
    auto addHill = [&](const char* name, float3 pos, float3 scale)
    {
        Transform t;
        t.setTranslation(pos);
        t.setScaling(scale);
        NodeID n = builder.addNode(SceneBuilder::Node{name, t.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, landHillID);
    };

    addLandFlat("LandDistant", float3(0.f, 0.5f, -88.f), float2(180.f, 70.f));
    addLandFlat("LandFarWest", float3(-78.f, 0.35f, -58.f), float2(55.f, 75.f), 18.f);
    addLandFlat("LandFarEast", float3(80.f, 0.35f, -52.f), float2(52.f, 70.f), -15.f);
    addHill("HillA", float3(-22.f, 3.5f, -62.f), float3(14.f, 8.f, 10.f));
    addHill("HillB", float3(18.f, 4.2f, -70.f), float3(12.f, 10.f, 14.f));
    addHill("HillC", float3(5.f, 2.8f, -55.f), float3(9.f, 5.f, 11.f));
    addHill("CliffW", float3(-40.f, 6.f, -75.f), float3(8.f, 14.f, 6.f));

    // Hero canvases: plane center, sphere left, cube right — none obscure the plane
    {
        Transform planeX;
        planeX.setTranslation(float3(0.f, 2.05f, 0.f));
        planeX.setRotationEulerDeg(float3(-90.f, 0.f, 0.f));
        planeX.setScaling(float3(3.4f, 3.4f, 1.f));
        NodeID n = builder.addNode(SceneBuilder::Node{"LessonPlane", planeX.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, planeID);
    }
    {
        Transform sphX;
        sphX.setTranslation(float3(-5.2f, 1.9f, 1.1f));
        NodeID n = builder.addNode(SceneBuilder::Node{"LessonSphere", sphX.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, sphereID);
    }
    {
        Transform cubeX;
        cubeX.setTranslation(float3(5.2f, 1.9f, 1.1f));
        cubeX.setRotationEulerDeg(float3(8.f, 28.f, -6.f));
        cubeX.setScaling(float3(1.45f));
        NodeID n = builder.addNode(SceneBuilder::Node{"LessonCube", cubeX.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, cubeID);
    }

    mOrbitTarget = float3(0.f, 2.05f, 0.f);
    mCamYaw = 0.12f;
    mCamPitch = 0.22f;
    mCamDist = 11.0f;
    mFlyPos = float3(0.f, 3.4f, 11.5f);

    auto pCam = Camera::create("VernacularCam");
    pCam->setPosition(mFlyPos);
    pCam->setTarget(mOrbitTarget);
    pCam->setUpVector(float3(0.f, 1.f, 0.f));
    pCam->setFocalLength(32.f);
    builder.addCamera(pCam);
    builder.setSelectedCamera(pCam);

    auto pKey = DistantLight::create("Key");
    pKey->setWorldDirection(float3(0.25f, -0.85f, -0.4f));
    pKey->setIntensity(float3(4.2f, 3.8f, 5.0f));
    pKey->setAngle(0.15f);
    builder.addLight(pKey);

    auto pFill = DistantLight::create("Fill");
    pFill->setWorldDirection(float3(-0.5f, -0.3f, -0.2f));
    pFill->setIntensity(float3(0.7f, 0.85f, 1.3f));
    pFill->setAngle(0.45f);
    builder.addLight(pFill);

    (void)pTargetFbo;
}

void VernacularViewport::buildVibrationScene(SceneBuilder& builder, const Fbo* pTargetFbo)
{
    auto pMatFloor = StandardMaterial::create(getDevice(), "Floor");
    pMatFloor->setBaseColor(float4(0.10f, 0.11f, 0.14f, 1.f));
    pMatFloor->setRoughness(0.92f);
    pMatFloor->setDoubleSided(true);

    auto pMatCube = StandardMaterial::create(getDevice(), "VibeCube");
    pMatCube->setBaseColor(float4(0.85f, 0.55f, 0.25f, 1.f));
    pMatCube->setRoughness(0.35f);
    pMatCube->setMetallic(0.15f);
    pMatCube->setDoubleSided(true);

    auto pMatLetter = StandardMaterial::create(getDevice(), "LetterCube");
    pMatLetter->setBaseColor(float4(0.95f, 0.9f, 0.75f, 1.f));
    pMatLetter->setRoughness(0.4f);
    pMatLetter->setDoubleSided(true);

    MeshID floorID = builder.addTriangleMesh(TriangleMesh::createQuad(float2(28.f)), pMatFloor);
    MeshID cubeID = builder.addTriangleMesh(TriangleMesh::createCube(float3(1.f)), pMatCube);
    MeshID letterID = builder.addTriangleMesh(TriangleMesh::createCube(float3(1.f)), pMatLetter);

    Transform floorXform;
    floorXform.setTranslation(float3(0.f, 0.f, 0.f));
    floorXform.setRotationEulerDeg(float3(-90.f, 0.f, 0.f));
    NodeID floorNode = builder.addNode(SceneBuilder::Node{"Floor", floorXform.getMatrix(), float4x4(), float4x4()});
    builder.addMeshInstance(floorNode, floorID);

    const float panelCenters[4] = {-6.f, -2.f, 2.f, 6.f};
    const int gridN = 5;
    const float spacing = 0.42f;
    const float cubeScale = 0.32f;
    int cubeIdx = 0;
    for (int p = 0; p < 4; ++p)
    {
        float cx = panelCenters[p];
        for (int j = 0; j < gridN; ++j)
        {
            for (int i = 0; i < gridN; ++i)
            {
                float x = cx + (i - (gridN - 1) * 0.5f) * spacing;
                float z = (j - (gridN - 1) * 0.5f) * spacing;
                addCubeInstance(builder, cubeID, float3(x, 0.2f, z), cubeScale, "mode" + std::to_string(cubeIdx++));
            }
        }
    }

    const char* lines[] = {"VIBRATION", "MODES OF", "CUBE"};
    const float letterScale = 0.16f;
    const float cell = 0.19f;
    const float lineGap = 1.55f;
    const float zTitle = -5.2f;
    const float yBase = 2.4f;

    for (int line = 0; line < 3; ++line)
    {
        const char* text = lines[line];
        int len = (int)std::strlen(text);
        float lineWidth = len * 6.f * cell;
        float x0 = -0.5f * lineWidth;
        float y0 = yBase - line * lineGap;

        for (int ci = 0; ci < len; ++ci)
        {
            const Glyph* g = findGlyph(text[ci]);
            if (!g)
                continue;
            for (int r = 0; r < 7; ++r)
            {
                for (int c = 0; c < 5; ++c)
                {
                    if (((g->rows[r] >> c) & 1) == 0)
                        continue;
                    float x = x0 + ci * 6.f * cell + c * cell;
                    float y = y0 - r * cell;
                    addCubeInstance(
                        builder,
                        letterID,
                        float3(x, y, zTitle),
                        letterScale,
                        "glyph" + std::to_string(line) + "_" + std::to_string(ci) + "_" + std::to_string(r * 5 + c)
                    );
                }
            }
        }
    }

    mOrbitTarget = float3(0.f, 1.2f, -0.5f);
    mCamYaw = 0.18f;
    mCamPitch = 0.28f;
    mCamDist = 12.5f;
    mFlyPos = float3(0.f, 3.5f, 12.f);

    auto pCam = Camera::create("VernacularCam");
    pCam->setPosition(mFlyPos);
    pCam->setTarget(mOrbitTarget);
    pCam->setUpVector(float3(0.f, 1.f, 0.f));
    pCam->setFocalLength(32.f);
    builder.addCamera(pCam);
    builder.setSelectedCamera(pCam);

    auto pKey = DistantLight::create("Key");
    pKey->setWorldDirection(float3(0.35f, -1.f, -0.45f));
    pKey->setIntensity(float3(5.f, 4.6f, 4.0f));
    pKey->setAngle(0.12f);
    builder.addLight(pKey);

    auto pFill = DistantLight::create("Fill");
    pFill->setWorldDirection(float3(-0.55f, -0.35f, -0.25f));
    pFill->setIntensity(float3(0.9f, 1.1f, 1.4f));
    pFill->setAngle(0.4f);
    builder.addLight(pFill);

    (void)pTargetFbo;
}

void VernacularViewport::buildVernacularScene(const Fbo* pTargetFbo)
{
    SceneBuilder builder(getDevice(), getSettings(), SceneBuilder::Flags::Default);

    if (mShowMode == ShowMode::TempleSchool)
        buildTempleScene(builder, pTargetFbo);
    else
        buildVibrationScene(builder, pTargetFbo);

    mpScene = builder.getScene();
    mpCamera = mpScene->getCamera();
    mpScene->setCameraControlsEnabled(false);
    mpScene->setCameraSpeed(4.f);

    float radius = mpScene->getSceneBounds().radius();
    mpCamera->setDepthRange(0.1f, std::max(200.f, radius * 2.f));
    if (pTargetFbo)
        mpCamera->setAspectRatio(float(pTargetFbo->getWidth()) / float(pTargetFbo->getHeight()));

    resolveMaterialIds();
    createRasterPass();
    updateCamera(0.f);
    mStatusMsg = (mShowMode == ShowMode::TempleSchool)
                     ? "Temple School | [ ] looks | RMB orbit | Tab move | F1 menus | F3 vibe | M mute"
                     : "Vibration Modes | [ ] chapters | V waves | RMB orbit | Tab move | F3 temple";
}

uint32_t VernacularViewport::materialIdByName(const std::string& name) const
{
    if (!mpScene)
        return 0xffffffffu;
    const uint32_t n = mpScene->getMaterialCount();
    for (uint32_t i = 0; i < n; ++i)
    {
        const ref<Material>& pMat = mpScene->getMaterial(MaterialID(i));
        if (pMat && pMat->getName() == name)
            return i;
    }
    return 0xffffffffu;
}

void VernacularViewport::resolveMaterialIds()
{
    mMatFloor = materialIdByName("Floor");
    mMatCube = materialIdByName("VibeCube");
    mMatLetter = materialIdByName("LetterCube");
    mMatSky = materialIdByName("Sky");
    mMatOcean = materialIdByName("Ocean");
    mMatLand = materialIdByName("Land");
    mMatCanvas = materialIdByName("LessonCanvas");
}

void VernacularViewport::createRasterPass()
{
    FALCOR_ASSERT(mpScene);
    ProgramDesc desc;
    desc.addShaderModules(mpScene->getShaderModules());
    desc.addShaderLibrary("Samples/VernacularViewport/VernacularViewport.3d.slang").vsEntry("vsMain").psEntry("psMain");
    desc.addTypeConformances(mpScene->getTypeConformances());
    mpRasterPass = RasterPass::create(getDevice(), desc, mpScene->getSceneDefines());
}

void VernacularViewport::updateCamera(float dt)
{
    if (!mpCamera)
        return;

    dt = std::clamp(dt, 0.f, 0.1f);

    if (mMoveMode == MoveMode::Fly)
    {
        float3 forward = lookDirFromYawPitch();
        float3 right = normalize(cross(forward, float3(0.f, 1.f, 0.f)));
        // Guard gimbal lock at extreme pitch.
        if (length(right) < 1e-4f)
            right = float3(1.f, 0.f, 0.f);
        float3 up = float3(0.f, 1.f, 0.f);
        float speed = mFlySpeed * (mKeyShift ? 3.5f : 1.f) * dt;
        if (mKeyW)
            mFlyPos += forward * speed;
        if (mKeyS)
            mFlyPos -= forward * speed;
        if (mKeyA)
            mFlyPos -= right * speed;
        if (mKeyD)
            mFlyPos += right * speed;
        if (mKeyE)
            mFlyPos += up * speed;
        if (mKeyQ)
            mFlyPos -= up * speed;
        mpCamera->setPosition(mFlyPos);
        mpCamera->setTarget(mFlyPos + forward);
        mpCamera->setUpVector(up);
        return;
    }

    float cp = std::cos(mCamPitch), sp = std::sin(mCamPitch);
    float cy = std::cos(mCamYaw), sy = std::sin(mCamYaw);
    float3 back = float3(sy * cp, sp, cy * cp);
    float3 eye = mOrbitTarget + back * mCamDist;
    mFlyPos = eye;
    mpCamera->setPosition(eye);
    mpCamera->setTarget(mOrbitTarget);
    mpCamera->setUpVector(float3(0.f, 1.f, 0.f));
}

void VernacularViewport::setPerFrameVars(const Fbo* /*pTargetFbo*/)
{
    auto var = mpRasterPass->getVars()->getRootVar();
    var["PerFrameCB"]["gShowMode"] = uint32_t(mShowMode);
    var["PerFrameCB"]["gChapter"] = mChapter;
    var["PerFrameCB"]["gTime"] = mTime;
    var["PerFrameCB"]["gVibeAmp"] = mVibeAmp;
    var["PerFrameCB"]["gVertexWaves"] = mVertexWaves ? 1u : 0u;
    var["PerFrameCB"]["gMatFloor"] = mMatFloor;
    var["PerFrameCB"]["gMatCube"] = mMatCube;
    var["PerFrameCB"]["gMatLetter"] = mMatLetter;
    var["PerFrameCB"]["gMatSky"] = mMatSky;
    var["PerFrameCB"]["gMatOcean"] = mMatOcean;
    var["PerFrameCB"]["gMatLand"] = mMatLand;
    var["PerFrameCB"]["gMatCanvas"] = mMatCanvas;
    var["PerFrameCB"]["gSunElev"] = mSunElev;
    var["PerFrameCB"]["gSunAzim"] = mSunAzim;
    var["PerFrameCB"]["gCloudCover"] = mCloudCover;
    var["PerFrameCB"]["gFogDensity"] = mFogDensity;
    var["PerFrameCB"]["gFogHeight"] = mFogHeight;
    var["PerFrameCB"]["gExposure"] = mExposure;
    var["PerFrameCB"]["gSkyIntensity"] = mSkyIntensity;
    var["PerFrameCB"]["gWaterScale"] = mWaterScale;
    var["PerFrameCB"]["gWaterChop"] = mWaterChop;
    var["PerFrameCB"]["gWaterAbsorb"] = mWaterAbsorb;
    var["PerFrameCB"]["gWaterColor"] = mWaterColor;
    var["PerFrameCB"]["gPadW"] = 0.f;
}

void VernacularViewport::onGuiRender(Gui* pGui)
{
    if (!mShowControls && !mShowStation)
        return;

    if (mShowControls)
    {
        Gui::Window w(pGui, "Temple / show", {380, 520}, {12, 12});
        w.text("VERNACULAR — docs/RUNBOOK.md");
        w.separator();

        Gui::DropdownList showList = {
            {uint32_t(ShowMode::TempleSchool), "Temple School"},
            {uint32_t(ShowMode::VibrationModes), "Vibration Modes (pinned)"},
        };
        uint32_t show = uint32_t(mShowMode);
        if (w.dropdown("Show mode", showList, show))
            switchShowMode(ShowMode(show));

        Gui::DropdownList moveList = {
            {uint32_t(MoveMode::Orbit), "Orbit — RMB drag, wheel zoom"},
            {uint32_t(MoveMode::Fly), "Fly — WASD QE, RMB look"},
        };
        uint32_t move = uint32_t(mMoveMode);
        if (w.dropdown("Movement", moveList, move))
            setMoveMode(MoveMode(move));
        w.text("Tab cycles Orbit / Fly");
        if (mMoveMode == MoveMode::Fly)
            w.var("Fly speed", mFlySpeed, 1.f, 40.f, 0.5f);

        if (w.button("< Prev"))
            mChapter = (mChapter + kChapterCount - 1) % kChapterCount;
        if (w.button("Next >", true))
            mChapter = (mChapter + 1) % kChapterCount;
        w.text(chapterName());
        w.checkbox("Animate time", mAnimate);

        if (mShowMode == ShowMode::VibrationModes)
        {
            w.checkbox("Vertex wave modulation", mVertexWaves);
            w.var("Vibe amplitude", mVibeAmp, 0.f, 1.f, 0.01f);
        }

        w.separator();
        w.text("Environment");
        w.var("Sun elevation", mSunElev, 0.f, 1.f, 0.01f);
        w.var("Sun azimuth", mSunAzim, 0.f, 1.f, 0.01f);
        w.var("Cloud cover", mCloudCover, 0.f, 1.f, 0.01f);
        w.var("Haze / fog", mFogDensity, 0.f, 0.12f, 0.001f);
        w.var("Fog height falloff", mFogHeight, 0.05f, 2.f, 0.01f);
        w.var("Sky intensity", mSkyIntensity, 0.2f, 2.5f, 0.01f);
        w.var("Exposure", mExposure, 0.3f, 2.5f, 0.01f);

        w.separator();
        w.text("Water");
        w.var("Wave scale", mWaterScale, 0.15f, 2.f, 0.01f);
        w.var("Chop", mWaterChop, 0.f, 1.5f, 0.01f);
        w.var("Absorption", mWaterAbsorb, 0.f, 1.5f, 0.01f);
        w.rgbColor("Water color", mWaterColor);

        w.separator();
        w.checkbox("Mute audio (M)", mAudioMute);
        w.text(mAudioStatus);
        if (!mStatusMsg.empty())
            w.text(mStatusMsg);

        updateAudioState();
    }

    if (mShowStation)
    {
        const auto& st = activeStation();
        Gui::Window s(pGui, "Station", {420, 280}, {410, 12});
        s.text(st.title);
        s.text(std::string("Stage: ") + st.stage);
        s.separator();
        s.textWrapped(st.blurb);
        s.textWrapped(std::string("Tip: ") + st.tip);
        s.separator();
        if (s.button("Prev [", true))
            mChapter = (mChapter + kChapterCount - 1) % kChapterCount;
        if (s.button("Next ]", true))
            mChapter = (mChapter + 1) % kChapterCount;
        updateAudioState();
    }
}

void VernacularViewport::onFrameRender(RenderContext* pRenderContext, const ref<Fbo>& pTargetFbo)
{
    const float4 clear = (mShowMode == ShowMode::TempleSchool) ? kClearTemple : kClearVibe;
    pRenderContext->clearFbo(pTargetFbo.get(), clear, 1.0f, 0, FboAttachmentType::All);

    double now = getGlobalClock().getTime();
    float dt = float(std::max(0.0, now - mLastFrameTime));
    mLastFrameTime = now;

    if (mAnimate)
        mTime = float(now);
    updateCamera(dt);
    updateAudioState();

    if (mpScene)
    {
        IScene::UpdateFlags updates = mpScene->update(pRenderContext, getGlobalClock().getTime());
        if (is_set(updates, IScene::UpdateFlags::GeometryChanged))
            FALCOR_THROW("VernacularViewport does not support scene geometry changes.");
        if (is_set(updates, IScene::UpdateFlags::RecompileNeeded))
            createRasterPass();

        setPerFrameVars(pTargetFbo.get());
        mpRasterPass->getState()->setFbo(pTargetFbo);
        mpScene->rasterize(
            pRenderContext,
            mpRasterPass->getState().get(),
            mpRasterPass->getVars().get(),
            RasterizerState::CullMode::None
        );
    }

    const auto& st = activeStation();
    std::ostringstream hud1;
    hud1 << "[" << (mChapter + 1) << "/" << kChapterCount << "] " << st.title;
    if (mShowMode == ShowMode::TempleSchool)
        hud1 << "  |  Temple";
    else
        hud1 << "  |  Vibration";
    hud1 << "  |  " << moveModeName();
    getTextRenderer().render(pRenderContext, asciiForHud(hud1.str()), pTargetFbo, {16, 16});
    if (!mShowControls && !mShowStation)
    {
        getTextRenderer().render(pRenderContext, asciiForHud(st.blurb), pTargetFbo, {16, 40});
        const char* moveHint = (mMoveMode == MoveMode::Orbit)
                                   ? "Orbit: RMB drag + wheel  |  Tab Fly  |  [ ] look  |  F1 menus  |  F3 show  |  M mute"
                                   : "Fly: WASD QE + RMB look  |  Tab Orbit  |  [ ] look  |  F1 menus  |  F3 show  |  M mute";
        getTextRenderer().render(pRenderContext, asciiForHud(moveHint), pTargetFbo, {16, 64});
    }
}

bool VernacularViewport::onKeyEvent(const KeyboardEvent& keyEvent)
{
    const bool down = keyEvent.type == KeyboardEvent::Type::KeyPressed;
    const bool up = keyEvent.type == KeyboardEvent::Type::KeyReleased;

    if (keyEvent.key == Input::Key::LeftShift || keyEvent.key == Input::Key::RightShift)
    {
        if (down)
            mKeyShift = true;
        if (up)
            mKeyShift = false;
        if (mMoveMode == MoveMode::Fly)
            return true;
    }

    auto trackFly = [&](Input::Key k, bool& flag)
    {
        if (keyEvent.key == k)
        {
            if (down)
                flag = true;
            if (up)
                flag = false;
            return mMoveMode == MoveMode::Fly;
        }
        return false;
    };
    if (trackFly(Input::Key::W, mKeyW))
        return true;
    if (trackFly(Input::Key::A, mKeyA))
        return true;
    if (trackFly(Input::Key::S, mKeyS))
        return true;
    if (trackFly(Input::Key::D, mKeyD))
        return true;
    if (trackFly(Input::Key::Q, mKeyQ))
        return true;
    if (trackFly(Input::Key::E, mKeyE))
        return true;

    if (keyEvent.type == KeyboardEvent::Type::KeyPressed)
    {
        if (keyEvent.key == Input::Key::Tab)
        {
            setMoveMode(mMoveMode == MoveMode::Orbit ? MoveMode::Fly : MoveMode::Orbit);
            return true;
        }
        if (keyEvent.key == Input::Key::F1)
        {
            mShowControls = !mShowControls;
            mStatusMsg = mShowControls ? "Menus on" : "Menus off";
            return true;
        }
        if (keyEvent.key == Input::Key::F2)
        {
            mShowStation = !mShowStation;
            mStatusMsg = mShowStation ? "Station on" : "Station off";
            return true;
        }
        if (keyEvent.key == Input::Key::F3)
        {
            switchShowMode(
                mShowMode == ShowMode::TempleSchool ? ShowMode::VibrationModes : ShowMode::TempleSchool
            );
            return true;
        }
        if (keyEvent.key == Input::Key::M)
        {
            mAudioMute = !mAudioMute;
            mStatusMsg = mAudioMute ? "Audio muted" : "Audio unmuted";
            updateAudioState();
            return true;
        }
        if (keyEvent.key == Input::Key::LeftBracket)
        {
            mChapter = (mChapter + kChapterCount - 1) % kChapterCount;
            updateAudioState();
            return true;
        }
        if (keyEvent.key == Input::Key::RightBracket)
        {
            mChapter = (mChapter + 1) % kChapterCount;
            updateAudioState();
            return true;
        }
        if (keyEvent.key == Input::Key::V && mShowMode == ShowMode::VibrationModes)
        {
            mVertexWaves = !mVertexWaves;
            mStatusMsg = mVertexWaves ? "Vertex waves ON" : "Vertex waves OFF";
            return true;
        }
        if (keyEvent.key == Input::Key::Comma && mShowMode == ShowMode::VibrationModes)
        {
            mVibeAmp = std::max(0.f, mVibeAmp - 0.03f);
            mStatusMsg = "Amp " + std::to_string(mVibeAmp);
            return true;
        }
        if (keyEvent.key == Input::Key::Period && mShowMode == ShowMode::VibrationModes)
        {
            mVibeAmp = std::min(1.f, mVibeAmp + 0.03f);
            mStatusMsg = "Amp " + std::to_string(mVibeAmp);
            return true;
        }
        if (keyEvent.key >= Input::Key::Key1 && keyEvent.key <= Input::Key::Key9)
        {
            mChapter = uint32_t(keyEvent.key) - uint32_t(Input::Key::Key1);
            updateAudioState();
            return true;
        }
        if (keyEvent.key == Input::Key::Key0)
        {
            mChapter = 9;
            updateAudioState();
            return true;
        }
        if (keyEvent.key == Input::Key::Minus)
        {
            mChapter = 10;
            updateAudioState();
            return true;
        }
        if (keyEvent.key == Input::Key::Equal)
        {
            // Cycle 11→12→13→14→15→11
            if (mChapter < 11 || mChapter >= 15)
                mChapter = 11;
            else
                mChapter = mChapter + 1;
            updateAudioState();
            return true;
        }
    }
    return false;
}

bool VernacularViewport::onMouseEvent(const MouseEvent& mouseEvent)
{
    // RMB look/orbit in both modes. Falcor pos is normalized [0,1] — see kLookGain.
    if (mouseEvent.type == MouseEvent::Type::ButtonDown && mouseEvent.button == Input::MouseButton::Right)
    {
        mLookDrag = true;
        mLastMouse = mouseEvent.pos;
        return true;
    }
    if (mouseEvent.type == MouseEvent::Type::ButtonUp && mouseEvent.button == Input::MouseButton::Right)
    {
        mLookDrag = false;
        return true;
    }
    if (mouseEvent.type == MouseEvent::Type::Move && mLookDrag)
    {
        float2 d = mouseEvent.pos - mLastMouse;
        mLastMouse = mouseEvent.pos;
        mCamYaw -= d.x * kLookGain;
        mCamPitch = std::clamp(mCamPitch + d.y * kLookGain, -1.2f, 1.35f);
        return true;
    }
    if (mouseEvent.type == MouseEvent::Type::Wheel && mMoveMode == MoveMode::Orbit)
    {
        float maxDist = (mShowMode == ShowMode::TempleSchool) ? 48.f : 28.f;
        mCamDist = std::clamp(mCamDist - mouseEvent.wheelDelta.y * kWheelZoom, 3.5f, maxDist);
        return true;
    }
    return false;
}

void VernacularViewport::onHotReload(HotReloadFlags reloaded)
{
    if (is_set(reloaded, HotReloadFlags::Program) && mpScene)
    {
        resolveMaterialIds();
        createRasterPass();
        mStatusMsg = "Hot-reloaded shaders";
    }
}

int runMain(int /*argc*/, char** /*argv*/)
{
    SampleAppConfig config;
    config.windowDesc.title = "VERNACULAR - Temple of Secret Knowledge";
    config.windowDesc.resizableWindow = true;
    config.windowDesc.width = 1680;
    config.windowDesc.height = 945;

    VernacularViewport app(config);
    return app.run();
}

int main(int argc, char** argv)
{
    return catchAndReportAllExceptions([&]() { return runMain(argc, argv); });
}

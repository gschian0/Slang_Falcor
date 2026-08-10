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
#include "Core/Platform/OS.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <random>
#include <sstream>
#include <string>
#include <vector>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
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
     "Singing-bowl / delta bed on the lesson plane (M mute). Orbit to hear distance + Doppler."},
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

const char* VernacularViewport::lightModeName() const
{
    switch (mLightMode)
    {
    case LightMode::Lambert:
        return "Lambert";
    case LightMode::Blinn:
        return "Blinn";
    case LightMode::Physical:
        return "Physical";
    default:
        return "Unlit";
    }
}

const char* VernacularViewport::upscaleModeName() const
{
    switch (mUpscaleMode)
    {
    case UpscaleMode::InternalScale:
        return "Internal scale";
    case UpscaleMode::TAA:
        return "TAA";
    case UpscaleMode::DLSS:
        return "DLSS (n/a)";
    default:
        return "Off";
    }
}

const char* VernacularViewport::dlssWhy() const
{
    return mDlssWhy.c_str();
}

bool VernacularViewport::usesInternalTarget() const
{
    if (mUpscaleMode == UpscaleMode::Off)
        return false;
    return true;
}

float VernacularViewport::internalScale() const
{
    if (mUpscaleMode == UpscaleMode::Off)
        return 1.f;
    if (mScaleIndex == 0)
        return 0.50f;
    if (mScaleIndex == 1)
        return 0.67f;
    return 1.f;
}

void VernacularViewport::cycleLightMode()
{
    mLightMode = LightMode((uint32_t(mLightMode) + 1u) % 4u);
    mStatusMsg = std::string("Lighting: ") + lightModeName();
}

void VernacularViewport::cycleUpscaleMode()
{
    uint32_t next = (uint32_t(mUpscaleMode) + 1u) % 4u;
    if (next == uint32_t(UpscaleMode::DLSS))
        next = uint32_t(UpscaleMode::Off); // skip unavailable
    mUpscaleMode = UpscaleMode(next);
    mResetTaa = true;
    mStatusMsg = std::string("Upscale: ") + upscaleModeName();
}

void VernacularViewport::captureCubeRotation()
{
    Transform rotOnly;
    rotOnly.setRotationEulerDeg(mCubeEulerDeg);
    const float4x4 M = rotOnly.getMatrix();
    const float4 xW = math::mul(M, float4(1.f, 0.f, 0.f, 0.f));
    const float4 yW = math::mul(M, float4(0.f, 1.f, 0.f, 0.f));
    const float4 zW = math::mul(M, float4(0.f, 0.f, 1.f, 0.f));
    mCubeRot0 = float3(xW.x, xW.y, xW.z);
    mCubeRot1 = float3(yW.x, yW.y, yW.z);
    mCubeRot2 = float3(zW.x, zW.y, zW.z);
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
    // Fail-soft: never throw / never block the GPU path if the endpoint is missing.
    mSoundscape.start();
}

void VernacularViewport::shutdownAudio()
{
    mSoundscape.stop();
}

void VernacularViewport::updateSoundscape(float dt)
{
    mSoundscape.setMuted(mAudioMute);
    mSoundscape.setMasterGain(mAudioMasterGain);
    mSoundscape.setDopplerEnabled(mAudioDoppler);

    if (!mpCamera)
        return;

    const float3 eye = mpCamera->getPosition();
    const float3 forward = lookDirFromYawPitch();
    const float3 up = float3(0.f, 1.f, 0.f);
    float3 vel = float3(0.f);
    if (mAudioHaveLastEye && dt > 1e-4f && dt < 0.25f)
        vel = (eye - mAudioLastEye) / dt;
    mAudioLastEye = eye;
    mAudioHaveLastEye = true;

    VernacularSoundscape::Listener listener;
    listener.position = {eye.x, eye.y, eye.z};
    listener.forward = {forward.x, forward.y, forward.z};
    listener.up = {up.x, up.y, up.z};
    listener.velocity = {vel.x, vel.y, vel.z};
    mSoundscape.setListener(listener);

    const float3 bowlPos = (mShowMode == ShowMode::TempleSchool) ? float3(0.f, 2.05f, 0.f) : float3(0.f, 1.2f, -0.5f);
    const float3 toBowl = bowlPos - eye;
    const float bowlDist = length(toBowl);
    const float3 bowlDir = (bowlDist > 1e-4f) ? (toBowl / bowlDist) : forward;
    const float lookAlign = std::clamp(dot(forward, bowlDir), 0.f, 1.f);
    const float nearF = std::clamp(1.f - bowlDist / 14.f, 0.f, 1.f);
    const float lookBoost = 0.70f + 0.50f * lookAlign + 0.30f * nearF;

    // Ch0 = classic ~120/122 Hz delta (~2 Hz beat). Other chapters: slight f0 shift, same source.
    const float f0 = 120.f + float(mChapter) * 3.25f;
    const float beat = std::clamp(2.0f + float(mChapter) * 0.07f, 0.5f, 4.f);

    VernacularSoundscape::Source bowl;
    bowl.enabled = true;
    bowl.kind = VernacularSoundscape::SourceKind::Bowl;
    bowl.position = {bowlPos.x, bowlPos.y, bowlPos.z};
    bowl.velocity = {0.f, 0.f, 0.f};
    bowl.freqs[0] = f0;
    bowl.freqs[1] = f0 + beat;
    bowl.freqs[2] = f0 * 2.01f;
    bowl.amps[0] = 0.09f;
    bowl.amps[1] = 0.09f;
    bowl.amps[2] = 0.028f;
    bowl.lookBoost = lookBoost;
    mSoundscape.setSource(VernacularSoundscape::kBowlSlot, bowl);

    VernacularSoundscape::Source atmosphere;
    atmosphere.enabled = (mShowMode == ShowMode::TempleSchool);
    atmosphere.kind = VernacularSoundscape::SourceKind::Atmosphere;
    atmosphere.position = {0.f, 12.f, -28.f}; // distant ocean/sky bed
    atmosphere.velocity = {0.f, 0.f, 0.f};
    atmosphere.amps[0] = 0.032f;
    atmosphere.lookBoost = 1.f;
    mSoundscape.setSource(VernacularSoundscape::kAtmosphereSlot, atmosphere);

    // Chirp hooks (slots 2–4): reserved / silent this pass.
    for (int i = 0; i < VernacularSoundscape::kChirpCount; ++i)
    {
        VernacularSoundscape::Source chirp;
        chirp.enabled = false;
        chirp.kind = VernacularSoundscape::SourceKind::ChirpHook;
        mSoundscape.setSource(VernacularSoundscape::kChirpSlot0 + i, chirp);
    }
}

void VernacularViewport::loadSchoolPaths()
{
    mDlssWhy =
        "DLSS: DLSSPass.dll + nvngx_dlss.dll ship next to this exe, but SampleApp has no Mogwai "
        "RenderData (color+depth+mvec+jitter). NGXWrapper is plugin-private. Use Mogwai PathTracer+DLSSPass "
        "-- NGX is the research SDK, not a hamster-wheel rewrite.";

    const auto runtime = getRuntimeDirectory();
    mEditorCmd = runtime / "vernacular_school_editor.cmd";
    mShaderLessons = runtime / "shaders" / "Samples" / "VernacularViewport" / "lessons";

    const auto pathsFile = runtime / "vernacular_school_paths.txt";
    if (std::filesystem::exists(pathsFile))
    {
        std::ifstream in(pathsFile);
        std::string line;
        while (std::getline(in, line))
        {
            if (line.empty() || line[0] == '#')
                continue;
            auto eq = line.find('=');
            if (eq == std::string::npos)
                continue;
            std::string key = line.substr(0, eq);
            std::string val = line.substr(eq + 1);
            while (!val.empty() && (val.back() == '\r' || val.back() == ' '))
                val.pop_back();
            if (key == "REPO_LESSONS")
                mRepoLessons = val;
            else if (key == "PYTHON")
                mPythonExe = val;
            else if (key == "REPO_ROOT")
                mRepoRoot = val;
        }
    }

    if (mRepoLessons.empty())
    {
        // Dev fallback: walk up from runtime toward native/samples/VernacularViewport/lessons
        auto p = runtime;
        for (int i = 0; i < 10 && p.has_parent_path(); ++i)
        {
            auto cand = p / "native" / "samples" / "VernacularViewport" / "lessons";
            if (std::filesystem::exists(cand / "temple_vs.slang"))
            {
                mRepoLessons = cand;
                mRepoRoot = p;
                break;
            }
            p = p.parent_path();
        }
    }
}

void VernacularViewport::syncLessonSourcesIfNeeded(bool force)
{
    if (mRepoLessons.empty() || mShaderLessons.empty())
        return;
    if (!std::filesystem::exists(mRepoLessons))
        return;
    std::filesystem::create_directories(mShaderLessons);

    bool copied = false;
    std::error_code ec;
    for (const auto& ent : std::filesystem::directory_iterator(mRepoLessons, ec))
    {
        if (!ent.is_regular_file())
            continue;
        auto dst = mShaderLessons / ent.path().filename();
        bool need = force || !std::filesystem::exists(dst);
        if (!need)
        {
            auto srcT = std::filesystem::last_write_time(ent.path(), ec);
            auto dstT = std::filesystem::last_write_time(dst, ec);
            need = srcT > dstT;
        }
        if (need)
        {
            std::filesystem::copy_file(ent.path(), dst, std::filesystem::copy_options::overwrite_existing, ec);
            copied = true;
        }
    }

    auto hostSrc = mRepoLessons.parent_path() / "VernacularViewport.3d.slang";
    auto hostDst = mShaderLessons.parent_path() / "VernacularViewport.3d.slang";
    if (std::filesystem::exists(hostSrc))
    {
        bool need = force || !std::filesystem::exists(hostDst);
        if (!need)
        {
            auto srcT = std::filesystem::last_write_time(hostSrc, ec);
            auto dstT = std::filesystem::last_write_time(hostDst, ec);
            need = srcT > dstT;
        }
        if (need)
        {
            std::filesystem::copy_file(hostSrc, hostDst, std::filesystem::copy_options::overwrite_existing, ec);
            copied = true;
        }
    }

    if (copied && mpScene)
    {
        createRasterPass();
        createSchoolPasses();
        mStatusMsg = "Synced school shaders (F5)";
    }
}

#ifdef _WIN32
static HWND gSchoolHwnd = nullptr;
static BOOL CALLBACK focusVernacularSchoolWnd(HWND hwnd, LPARAM)
{
    wchar_t title[320];
    if (GetWindowTextW(hwnd, title, 320) <= 0)
        return TRUE;
    if (wcsstr(title, L"VERNACULAR") && wcsstr(title, L"3D school"))
    {
        gSchoolHwnd = hwnd;
        return FALSE;
    }
    return TRUE;
}
#endif

void VernacularViewport::openSchoolEditor()
{
#ifdef _WIN32
    gSchoolHwnd = nullptr;
    EnumWindows(focusVernacularSchoolWnd, 0);
    if (gSchoolHwnd)
    {
        ShowWindow(gSchoolHwnd, SW_RESTORE);
        SetForegroundWindow(gSchoolHwnd);
        mStatusMsg = "Focused shader school window";
        return;
    }
#endif

    if (!mEditorCmd.empty() && std::filesystem::exists(mEditorCmd))
    {
#ifdef _WIN32
        ShellExecuteW(nullptr, L"open", mEditorCmd.wstring().c_str(), nullptr,
                      mRepoRoot.empty() ? nullptr : mRepoRoot.wstring().c_str(), SW_SHOWNORMAL);
#else
        executeProcess("cmd", std::string("/c \"") + mEditorCmd.string() + "\"");
#endif
        mStatusMsg = "Opened shader school (VS / PS / Diff)";
        return;
    }

    if (!mPythonExe.empty() && !mRepoLessons.empty())
    {
        std::ostringstream args;
        args << "-m slang_falcon.live --no-curriculum --school-3d --entry hello_pixel --size 512"
             << " --files \"" << (mRepoLessons / "temple_vs.slang").string() << "\""
             << " \"" << (mRepoLessons / "temple_ps.slang").string() << "\""
             << " \"" << (mRepoLessons / "temple_diff.slang").string() << "\""
             << " --labels VS,PS,Diff";
        std::string py = mPythonExe.string();
        if (py.size() > 4 && py.substr(py.size() - 4) == ".exe")
            py = py.substr(0, py.size() - 4);
        try
        {
            executeProcess(py, args.str());
            mStatusMsg = "Opened shader school (VS / PS / Diff)";
        }
        catch (...)
        {
            mStatusMsg = "School editor failed — check vernacular_school_paths.txt";
        }
        return;
    }

    mStatusMsg = "School editor missing — rebuild with sync_vernacular_viewport.ps1 -Build";
}

void VernacularViewport::createSchoolPasses()
{
    auto pDev = getDevice();
    if (!mpLinearSampler)
    {
        Sampler::Desc sd;
        sd.setFilterMode(TextureFilteringMode::Linear, TextureFilteringMode::Linear, TextureFilteringMode::Linear);
        mpLinearSampler = pDev->createSampler(sd);
    }
    try
    {
        mpMvecPass = FullScreenPass::create(pDev, "Samples/VernacularViewport/lessons/mvec.ps.slang");
        mpTaaPass = FullScreenPass::create(pDev, "Samples/VernacularViewport/lessons/taa.ps.slang");
        mpBlitPass = FullScreenPass::create(pDev, "Samples/VernacularViewport/lessons/upscale_blit.ps.slang");
        mpBoidsCs = ComputePass::create(pDev, "Samples/VernacularViewport/lessons/boids.cs.slang", "main");
        ProgramDesc boidDesc;
        boidDesc.addShaderLibrary("Samples/VernacularViewport/lessons/boids.3d.slang").vsEntry("vsMain").psEntry("psMain");
        mpBoidPass = RasterPass::create(pDev, boidDesc);
        mpBoidPass->getState()->setVao(Vao::create(Vao::Topology::TriangleList));
        DepthStencilState::Desc ds;
        ds.setDepthEnabled(true).setDepthWriteMask(true).setDepthFunc(ComparisonFunc::Less);
        mpBoidPass->getState()->setDepthStencilState(DepthStencilState::create(ds));
        RasterizerState::Desc rs;
        rs.setCullMode(RasterizerState::CullMode::None);
        mpBoidPass->getState()->setRasterizerState(RasterizerState::create(rs));
    }
    catch (const std::exception& e)
    {
        logWarning("VernacularViewport school passes: {}", e.what());
        mStatusMsg = std::string("School pass compile: ") + e.what();
    }
}

void VernacularViewport::initBoids()
{
    struct BoidCPU
    {
        float pos[3];
        float pad0;
        float vel[3];
        float pad1;
    };
    std::vector<BoidCPU> init(kBoidCount);
    std::mt19937 rng(7);
    std::uniform_real_distribution<float> dx(-12.f, 12.f);
    std::uniform_real_distribution<float> dy(-2.5f, 4.5f);
    std::uniform_real_distribution<float> dz(-10.f, 8.f);
    std::uniform_real_distribution<float> dv(-1.2f, 1.2f);
    for (uint32_t i = 0; i < kBoidCount; ++i)
    {
        init[i].pos[0] = mBoidOrigin.x + dx(rng);
        init[i].pos[1] = mBoidOrigin.y + dy(rng);
        init[i].pos[2] = mBoidOrigin.z + dz(rng);
        init[i].vel[0] = dv(rng);
        init[i].vel[1] = dv(rng) * 0.35f;
        init[i].vel[2] = dv(rng);
        init[i].pad0 = init[i].pad1 = 0.f;
    }
    auto flags = ResourceBindFlags::ShaderResource | ResourceBindFlags::UnorderedAccess;
    mpBoids[0] = getDevice()->createStructuredBuffer(
        uint32_t(sizeof(BoidCPU)), kBoidCount, flags, MemoryType::DeviceLocal, init.data(), false
    );
    mpBoids[1] = getDevice()->createStructuredBuffer(
        uint32_t(sizeof(BoidCPU)), kBoidCount, flags, MemoryType::DeviceLocal, init.data(), false
    );
    mBoidSrc = 0;
}

void VernacularViewport::ensureUpscaleTargets(uint32_t displayW, uint32_t displayH)
{
    if (displayW == 0 || displayH == 0)
        return;
    mDisplayW = displayW;
    mDisplayH = displayH;
    const float s = internalScale();
    uint32_t iw = std::max(16u, uint32_t(std::lround(float(displayW) * s)));
    uint32_t ih = std::max(16u, uint32_t(std::lround(float(displayH) * s)));
    if (mpSceneFbo && iw == mInternalW && ih == mInternalH)
        return;

    mInternalW = iw;
    mInternalH = ih;
    Fbo::Desc desc;
    desc.setColorTarget(0, ResourceFormat::RGBA16Float);
    desc.setDepthStencilTarget(ResourceFormat::D32Float);
    mpSceneFbo = Fbo::create2D(getDevice(), iw, ih, desc);

    Fbo::Desc mvecDesc;
    mvecDesc.setColorTarget(0, ResourceFormat::RG16Float);
    mpMvecFbo = Fbo::create2D(getDevice(), iw, ih, mvecDesc);

    Fbo::Desc taaDesc;
    taaDesc.setColorTarget(0, ResourceFormat::RGBA16Float);
    mpTaaFbo = Fbo::create2D(getDevice(), iw, ih, taaDesc);

    mpPrevColor = getDevice()->createTexture2D(
        iw, ih, ResourceFormat::RGBA16Float, 1, 1, nullptr,
        ResourceBindFlags::ShaderResource | ResourceBindFlags::RenderTarget
    );
    mResetTaa = true;
}

void VernacularViewport::dispatchBoids(RenderContext* pRenderContext, float dt)
{
    if (!mBoidsEnabled || !mpBoidsCs || !mpBoids[0] || mShowMode != ShowMode::TempleSchool)
        return;
    auto var = mpBoidsCs->getRootVar();
    var["gIn"] = mpBoids[mBoidSrc];
    var["gOut"] = mpBoids[1 - mBoidSrc];
    var["PerFrameCB"]["gCount"] = kBoidCount;
    var["PerFrameCB"]["gDt"] = dt;
    var["PerFrameCB"]["gTime"] = mTime;
    var["PerFrameCB"]["gOrigin"] = mBoidOrigin;
    var["PerFrameCB"]["gRadius"] = mBoidRadius;
    mpBoidsCs->execute(pRenderContext, kBoidCount, 1, 1);
    mBoidSrc = 1 - mBoidSrc;
}

void VernacularViewport::drawBoids(RenderContext* pRenderContext, const ref<Fbo>& pFbo)
{
    if (!mBoidsEnabled || !mpBoidPass || !mpBoids[mBoidSrc] || !mpCamera || mShowMode != ShowMode::TempleSchool)
        return;
    const float3 eye = mpCamera->getPosition();
    const float3 fwd = lookDirFromYawPitch();
    float3 right = normalize(cross(fwd, float3(0.f, 1.f, 0.f)));
    if (length(right) < 1e-4f)
        right = float3(1.f, 0.f, 0.f);
    const float3 up = normalize(cross(right, fwd));

    auto var = mpBoidPass->getRootVar();
    var["gBoids"] = mpBoids[mBoidSrc];
    var["PerFrameCB"]["gViewProj"] = mpCamera->getViewProjMatrix();
    var["PerFrameCB"]["gCamPos"] = eye;
    var["PerFrameCB"]["gSize"] = 0.11f;
    var["PerFrameCB"]["gCamRight"] = right;
    var["PerFrameCB"]["gTime"] = mTime;
    var["PerFrameCB"]["gCamUp"] = up;
    var["PerFrameCB"]["gCount"] = kBoidCount;
    mpBoidPass->getState()->setFbo(pFbo);
    mpBoidPass->draw(pRenderContext, kBoidCount * 6, 0);
}

void VernacularViewport::applyUpscale(RenderContext* pRenderContext, const ref<Fbo>& pSceneFbo, const ref<Fbo>& pTargetFbo)
{
    const auto& pColor = pSceneFbo->getColorTexture(0);
    const auto& pDepth = pSceneFbo->getDepthStencilTexture();
    ref<Texture> pPresent = pColor;

    const bool wantTaa = (mUpscaleMode == UpscaleMode::TAA) && mpTaaPass && mpMvecPass && mpMvecFbo && mpTaaFbo && mpPrevColor && pDepth;

    if (wantTaa && mpCamera)
    {
        const float4x4 viewProj = mpCamera->getViewProjMatrix();
        const float4x4 invVP = mpCamera->getInvViewProjMatrix();
        const float4x4 prevVP = mHavePrevViewProj ? mPrevViewProj : viewProj;

        {
            auto var = mpMvecPass->getRootVar();
            var["PerFrameCB"]["gInvViewProj"] = invVP;
            var["PerFrameCB"]["gPrevViewProj"] = prevVP;
            var["gDepth"] = pDepth;
            var["gSampler"] = mpLinearSampler;
            mpMvecPass->execute(pRenderContext, mpMvecFbo);
        }
        {
            auto var = mpTaaPass->getRootVar();
            var["PerFrameCB"]["gAlpha"] = mResetTaa ? 1.f : 0.1f;
            var["PerFrameCB"]["gColorBoxSigma"] = 1.f;
            var["PerFrameCB"]["gAntiFlicker"] = 1u;
            var["gTexColor"] = pColor;
            var["gTexMotionVec"] = mpMvecFbo->getColorTexture(0);
            var["gTexPrevColor"] = mpPrevColor;
            var["gSampler"] = mpLinearSampler;
            mpTaaPass->execute(pRenderContext, mpTaaFbo);
        }
        pPresent = mpTaaFbo->getColorTexture(0);
        pRenderContext->blit(pPresent->getSRV(), mpPrevColor->getRTV());
        mResetTaa = false;
        mPrevViewProj = viewProj;
        mHavePrevViewProj = true;
    }
    else
    {
        mResetTaa = true;
    }

    if (mpBlitPass && (mBicubicBlit || pPresent->getWidth() != pTargetFbo->getWidth()))
    {
        auto var = mpBlitPass->getRootVar();
        var["PerFrameCB"]["gBicubic"] = mBicubicBlit ? 1u : 0u;
        var["gSrc"] = pPresent;
        var["gSampler"] = mpLinearSampler;
        mpBlitPass->execute(pRenderContext, pTargetFbo);
    }
    else
    {
        pRenderContext->blit(
            pPresent->getSRV(),
            pTargetFbo->getRenderTargetView(0),
            RenderContext::kMaxRect,
            RenderContext::kMaxRect,
            TextureFilteringMode::Linear
        );
    }
}

void VernacularViewport::onLoad(RenderContext* /*pRenderContext*/)
{
    loadSchoolPaths();
    initAudio();
    buildVernacularScene(getTargetFbo().get());
    createSchoolPasses();
    initBoids();
    mLastFrameTime = getGlobalClock().getTime();
    mAudioHaveLastEye = false;
    if (const auto* fbo = getTargetFbo().get())
        ensureUpscaleTargets(fbo->getWidth(), fbo->getHeight());
}

void VernacularViewport::onShutdown()
{
    shutdownAudio();
}

void VernacularViewport::onResize(uint32_t width, uint32_t height)
{
    if (mpCamera && height > 0)
        mpCamera->setAspectRatio(float(width) / float(height));
    ensureUpscaleTargets(width, height);
    mResetTaa = true;
}

void VernacularViewport::switchShowMode(ShowMode mode)
{
    if (mShowMode == mode)
        return;
    mShowMode = mode;
    buildVernacularScene(getTargetFbo().get());
    mAudioHaveLastEye = false; // avoid a one-frame Doppler spike after the camera jump
    mStatusMsg = (mode == ShowMode::TempleSchool) ? "Show: Temple School" : "Show: Vibration Modes (pinned)";
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

    // Hero canvases: square plane center, sphere left, cube right — none obscure the plane.
    // Unit XZ quad * uniform scale, then -90 X → vertical XY square (Z scale used to be 1 → short rectangle).
    mPlaneCenter = float3(0.f, 2.05f, 0.f);
    mPlaneSize = 3.4f;
    mSphereCenter = float3(-5.2f, 1.9f, 1.1f);
    mSphereRadius = 0.85f;
    mCubeCenter = float3(5.2f, 1.9f, 1.1f);
    mCubeSize = 1.45f;
    mCubeEulerDeg = float3(8.f, 28.f, -6.f);
    captureCubeRotation();
    {
        Transform planeX;
        planeX.setTranslation(mPlaneCenter);
        planeX.setRotationEulerDeg(float3(-90.f, 0.f, 0.f));
        planeX.setScaling(float3(mPlaneSize));
        NodeID n = builder.addNode(SceneBuilder::Node{"LessonPlane", planeX.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, planeID);
    }
    {
        Transform sphX;
        sphX.setTranslation(mSphereCenter);
        NodeID n = builder.addNode(SceneBuilder::Node{"LessonSphere", sphX.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, sphereID);
    }
    {
        Transform cubeX;
        cubeX.setTranslation(mCubeCenter);
        cubeX.setRotationEulerDeg(mCubeEulerDeg);
        cubeX.setScaling(float3(mCubeSize));
        NodeID n = builder.addNode(SceneBuilder::Node{"LessonCube", cubeX.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, cubeID);
    }

    mOrbitTarget = mPlaneCenter;
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
                     ? "Temple School | [ ] looks | L light | U upscale | B boids | F8 edit | F1 menus | F3 vibe | M mute"
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
    var["PerFrameCB"]["gLightMode"] = uint32_t(mLightMode);
    var["PerFrameCB"]["gPlaneCenter"] = mPlaneCenter;
    var["PerFrameCB"]["gPlaneSize"] = mPlaneSize;
    var["PerFrameCB"]["gSphereCenter"] = mSphereCenter;
    var["PerFrameCB"]["gSphereRadius"] = mSphereRadius;
    var["PerFrameCB"]["gCubeCenter"] = mCubeCenter;
    var["PerFrameCB"]["gCubeSize"] = mCubeSize;
    var["PerFrameCB"]["gCubeRot0"] = mCubeRot0;
    var["PerFrameCB"]["gPadR0"] = 0.f;
    var["PerFrameCB"]["gCubeRot1"] = mCubeRot1;
    var["PerFrameCB"]["gPadR1"] = 0.f;
    var["PerFrameCB"]["gCubeRot2"] = mCubeRot2;
    var["PerFrameCB"]["gPadR2"] = 0.f;
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

        Gui::DropdownList lightList = {
            {uint32_t(LightMode::Unlit), "Unlit — raw look"},
            {uint32_t(LightMode::Lambert), "Lambert — N.L temple sun"},
            {uint32_t(LightMode::Blinn), "Blinn — specular temple sun"},
            {uint32_t(LightMode::Physical), "Physical — GGX temple sun"},
        };
        uint32_t light = uint32_t(mLightMode);
        if (w.dropdown("Lighting mode", lightList, light))
            mLightMode = LightMode(light);
        w.text("L cycles lighting (same sun as sky / ocean)");

        w.separator();
        w.text("Upscale — render low, reconstruct high");
        Gui::DropdownList upList = {
            {uint32_t(UpscaleMode::Off), "Off — native res"},
            {uint32_t(UpscaleMode::InternalScale), "Internal scale + blit"},
            {uint32_t(UpscaleMode::TAA), "TAA (depth mvec + history)"},
            {uint32_t(UpscaleMode::DLSS), "DLSS (unavailable)"},
        };
        uint32_t up = uint32_t(mUpscaleMode);
        if (w.dropdown("Upscale", upList, up))
        {
            if (up == uint32_t(UpscaleMode::DLSS))
            {
                mStatusMsg = mDlssWhy;
            }
            else
            {
                mUpscaleMode = UpscaleMode(up);
                mResetTaa = true;
                if (mDisplayW && mDisplayH)
                    ensureUpscaleTargets(mDisplayW, mDisplayH);
            }
        }
        w.tooltip(mDlssWhy, true);
        w.text(mDlssWhy);
        if (mUpscaleMode != UpscaleMode::Off)
        {
            Gui::DropdownList scaleList = {
                {0, "0.50 internal"},
                {1, "0.67 internal"},
                {2, "1.00 internal"},
            };
            if (w.dropdown("Internal scale", scaleList, mScaleIndex))
            {
                mResetTaa = true;
                if (mDisplayW && mDisplayH)
                    ensureUpscaleTargets(mDisplayW, mDisplayH);
            }
            w.checkbox("Bicubic blit (else bilinear)", mBicubicBlit);
        }

        w.separator();
        w.checkbox("Boids (compute flock)", mBoidsEnabled);
        w.text("B toggle — CS agents, VS/PS impostors. Research engines run flocks on compute.");
        if (w.button("Open editor window (F8)"))
            openSchoolEditor();
        w.text("E is Fly-up — school editor is F8 / this button. VS + PS + Diff tabs.");

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
        w.text("Spatial audio");
        w.checkbox("Mute audio (M)", mAudioMute);
        w.checkbox("Doppler", mAudioDoppler);
        w.var("Master gain", mAudioMasterGain, 0.f, 2.f, 0.01f);
        w.text(mSoundscape.status());
        w.text(mSoundscape.debugLine());
        if (!mStatusMsg.empty())
            w.text(mStatusMsg);
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
        s.textWrapped(
            "School passes: VS = vibration/placement (temple_vs). PS = looks + L lighting "
            "(temple_ps). Compute = B boids. Diff = temple_diff in live (bwd_diff labs, not 3D raster). "
            "Upscale = F1 Off / Internal / TAA — DLSS is NGX, not a rewrite."
        );
        if (s.button("Open editor window (F8)"))
            openSchoolEditor();
        s.separator();
        if (s.button("Prev [", true))
            mChapter = (mChapter + kChapterCount - 1) % kChapterCount;
        if (s.button("Next ]", true))
            mChapter = (mChapter + 1) % kChapterCount;
    }
}

void VernacularViewport::onFrameRender(RenderContext* pRenderContext, const ref<Fbo>& pTargetFbo)
{
    const float4 clear = (mShowMode == ShowMode::TempleSchool) ? kClearTemple : kClearVibe;

    double now = getGlobalClock().getTime();
    float dt = float(std::max(0.0, now - mLastFrameTime));
    mLastFrameTime = now;

    if (now - mLastLessonPoll > 0.45)
    {
        mLastLessonPoll = now;
        syncLessonSourcesIfNeeded(false);
    }

    if (mAnimate)
        mTime = float(now);
    updateCamera(dt);
    updateSoundscape(dt);
    dispatchBoids(pRenderContext, dt);

    ensureUpscaleTargets(pTargetFbo->getWidth(), pTargetFbo->getHeight());
    const bool internal = usesInternalTarget() && mpSceneFbo;
    const ref<Fbo>& pDrawFbo = internal ? mpSceneFbo : pTargetFbo;

    pRenderContext->clearFbo(pDrawFbo.get(), clear, 1.0f, 0, FboAttachmentType::All);
    if (internal)
        pRenderContext->clearFbo(pTargetFbo.get(), clear, 1.0f, 0, FboAttachmentType::All);

    if (mpScene)
    {
        IScene::UpdateFlags updates = mpScene->update(pRenderContext, getGlobalClock().getTime());
        if (is_set(updates, IScene::UpdateFlags::GeometryChanged))
            FALCOR_THROW("VernacularViewport does not support scene geometry changes.");
        if (is_set(updates, IScene::UpdateFlags::RecompileNeeded))
            createRasterPass();

        setPerFrameVars(pDrawFbo.get());
        mpRasterPass->getState()->setFbo(pDrawFbo);
        mpScene->rasterize(
            pRenderContext,
            mpRasterPass->getState().get(),
            mpRasterPass->getVars().get(),
            RasterizerState::CullMode::None
        );
        drawBoids(pRenderContext, pDrawFbo);
    }

    if (internal)
        applyUpscale(pRenderContext, pDrawFbo, pTargetFbo);
    else if (mpCamera)
    {
        mPrevViewProj = mpCamera->getViewProjMatrix();
        mHavePrevViewProj = true;
    }

    const auto& st = activeStation();
    std::ostringstream hud1;
    hud1 << "[" << (mChapter + 1) << "/" << kChapterCount << "] " << st.title;
    if (mShowMode == ShowMode::TempleSchool)
        hud1 << "  |  Temple";
    else
        hud1 << "  |  Vibration";
    hud1 << "  |  " << moveModeName();
    if (mShowMode == ShowMode::TempleSchool)
        hud1 << "  |  " << lightModeName();
    hud1 << "  |  " << upscaleModeName();
    if (mBoidsEnabled && mShowMode == ShowMode::TempleSchool)
        hud1 << "  |  Boids";
    getTextRenderer().render(pRenderContext, asciiForHud(hud1.str()), pTargetFbo, {16, 16});
    if (!mShowControls && !mShowStation)
    {
        getTextRenderer().render(pRenderContext, asciiForHud(st.blurb), pTargetFbo, {16, 40});
        const char* moveHint = (mMoveMode == MoveMode::Orbit)
                                   ? "Orbit: RMB + wheel  |  Tab Fly  |  [ ] look  |  L light  |  F1 menus  |  F3 show  |  F8 edit  |  B boids  |  M mute"
                                   : "Fly: WASD QE + RMB  |  Tab Orbit  |  [ ] look  |  L light  |  F1 menus  |  F3 show  |  F8 edit  |  B boids  |  M mute";
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
            return true;
        }
        if (keyEvent.key == Input::Key::L)
        {
            cycleLightMode();
            return true;
        }
        if (keyEvent.key == Input::Key::F8)
        {
            openSchoolEditor();
            return true;
        }
        if (keyEvent.key == Input::Key::B)
        {
            mBoidsEnabled = !mBoidsEnabled;
            mStatusMsg = mBoidsEnabled ? "Boids ON (compute flock)" : "Boids OFF";
            return true;
        }
        if (keyEvent.key == Input::Key::U)
        {
            cycleUpscaleMode();
            if (mDisplayW && mDisplayH)
                ensureUpscaleTargets(mDisplayW, mDisplayH);
            return true;
        }
        if (keyEvent.key == Input::Key::LeftBracket)
        {
            mChapter = (mChapter + kChapterCount - 1) % kChapterCount;
            return true;
        }
        if (keyEvent.key == Input::Key::RightBracket)
        {
            mChapter = (mChapter + 1) % kChapterCount;
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
            return true;
        }
        if (keyEvent.key == Input::Key::Key0)
        {
            mChapter = 9;
            return true;
        }
        if (keyEvent.key == Input::Key::Minus)
        {
            mChapter = 10;
            return true;
        }
        if (keyEvent.key == Input::Key::Equal)
        {
            // Cycle 11→12→13→14→15→11
            if (mChapter < 11 || mChapter >= 15)
                mChapter = 11;
            else
                mChapter = mChapter + 1;
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
    syncLessonSourcesIfNeeded(true);
    if (is_set(reloaded, HotReloadFlags::Program) && mpScene)
    {
        resolveMaterialIds();
        createRasterPass();
        createSchoolPasses();
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

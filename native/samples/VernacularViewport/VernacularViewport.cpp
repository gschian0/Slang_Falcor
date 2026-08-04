// VERNACULAR abstract studio - lesson cube on island, ocean/sky, orbit camera.
#include "VernacularViewport.h"


#include "Scene/SceneBuilder.h"
#include "Scene/TriangleMesh.h"
#include "Scene/Material/StandardMaterial.h"
#include "Scene/Lights/Light.h"
#include "Scene/Camera/Camera.h"
#include "Scene/Transform.h"
#include "Utils/UI/TextRenderer.h"
#include "Core/API/RasterizerState.h"
#include "Utils/Math/Matrix.h"

#include <algorithm>
#include <string>
#include <cmath>
#include <cstring>
#include <fstream>
#include <sstream>
#include <vector>

#if FALCOR_WINDOWS
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

#endif

namespace
{
// Falcor TextRenderer is ASCII-glyph only; UTF-8 lead bytes index past the atlas
// and dump the printable set (e.g. !"#$%&...). Keep HUD strings in 0x20-0x7E.
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
} // namespace

FALCOR_EXPORT_D3D12_AGILITY_SDK

namespace
{
    const float4 kClearColor(0.02f, 0.05f, 0.10f, 1.f);
    constexpr float kPi = 3.14159265f;

    float4x4 trs(const float3& t, float yaw, const float3& s)
    {
        Transform x;
        x.setTranslation(t);
        x.setRotationEuler(float3(0.f, yaw, 0.f));
        x.setScaling(s);
        return x.getMatrix();
    }

    float4x4 trsEuler(const float3& t, const float3& eulerDeg, const float3& s)
    {
        Transform x;
        x.setTranslation(t);
        x.setRotationEulerDeg(eulerDeg);
        x.setScaling(s);
        return x.getMatrix();
    }

    float3 effectiveScale(bool active, const float3& s)
    {
        return active ? s : s * 0.001f;
    }

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
}

VernacularViewport::VernacularViewport(const SampleAppConfig& config) : SampleApp(config) {}

void VernacularViewport::discoverRepoPaths()
{
    std::filesystem::path p = getRuntimeDirectory();
    for (int i = 0; i < 12; ++i)
    {
        if (std::filesystem::exists(p / "pyproject.toml") && std::filesystem::exists(p / "native"))
        {
            mRepoRoot = p;
            break;
        }
        if (!p.has_parent_path() || p == p.parent_path())
            break;
        p = p.parent_path();
    }
    if (!mRepoRoot.empty())
    {
        mVenvPython = mRepoRoot / ".venv" / "Scripts" / "python.exe";
        if (!std::filesystem::exists(mVenvPython))
            mVenvPython = mRepoRoot / ".venv" / "bin" / "python";
    }
}

void VernacularViewport::openLessonsWindow(const std::string& lessonSpec)
{
#if FALCOR_WINDOWS
    if (!std::filesystem::exists(mVenvPython))
    {
        mStatusMsg = "No venv python - see docs/RUNBOOK.md";
        return;
    }
    std::string cmd = "\"" + mVenvPython.string() + "\" -m slang_falcon.live";
    if (!lessonSpec.empty())
        cmd += " --lesson " + lessonSpec;
    STARTUPINFOA si{};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi{};
    std::string workDir = mRepoRoot.string();
    std::vector<char> cmdline(cmd.begin(), cmd.end());
    cmdline.push_back('\0');
    BOOL ok = CreateProcessA(
        nullptr, cmdline.data(), nullptr, nullptr, FALSE, CREATE_NEW_CONSOLE, nullptr, workDir.c_str(), &si, &pi
    );
    if (ok)
    {
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        mStatusMsg = lessonSpec.empty() ? "Opened lessons" : ("Opened " + lessonSpec);
    }
    else
        mStatusMsg = "CreateProcess failed for lessons";
#else
    mStatusMsg = "Open Lessons is Windows-only in this build";
#endif
}

void VernacularViewport::cycleLightPreset()
{
    mLightPreset = (mLightPreset + 1) % 4;
    switch (mLightPreset)
    {
    case 0:
        mSunElev = 0.42f;
        mSunAzim = 0.22f;
        mCloudCover = 0.35f;
        mFogDensity = 0.01f;
        mFogHeight = 0.4f;
        mLightWarm = 0.7f;
        mLightCool = 0.45f;
        mExposure = 1.0f;
        mStatusMsg = "Preset: Day clear";
        break;
    case 1:
        mSunElev = 0.12f;
        mSunAzim = 0.08f;
        mCloudCover = 0.55f;
        mFogDensity = 0.028f;
        mFogHeight = 0.55f;
        mLightWarm = 1.35f;
        mLightCool = 0.35f;
        mExposure = 1.15f;
        mStatusMsg = "Preset: Golden hour";
        break;
    case 2:
        mSunElev = 0.28f;
        mSunAzim = 0.55f;
        mCloudCover = 0.92f;
        mFogDensity = 0.055f;
        mFogHeight = 0.25f;
        mLightWarm = 0.35f;
        mLightCool = 1.1f;
        mExposure = 0.9f;
        mStatusMsg = "Preset: Storm fog";
        break;
    default:
        mSunElev = 0.05f;
        mSunAzim = 0.7f;
        mCloudCover = 0.4f;
        mFogDensity = 0.04f;
        mFogHeight = 0.6f;
        mLightWarm = 0.55f;
        mLightCool = 1.6f;
        mExposure = 1.25f;
        mStatusMsg = "Preset: Neon night";
        break;
    }
}

void VernacularViewport::onLoad(RenderContext* /*pRenderContext*/)
{
    discoverRepoPaths();
    buildVernacularScene(getTargetFbo().get());
}

void VernacularViewport::onResize(uint32_t width, uint32_t height)
{
    if (mpCamera && height > 0)
        mpCamera->setAspectRatio(float(width) / float(height));
}

void VernacularViewport::buildVernacularScene(const Fbo* pTargetFbo)
{
    SceneBuilder builder(getDevice(), getSettings(), SceneBuilder::Flags::Default);

    auto pMatSky = StandardMaterial::create(getDevice(), "Sky");
    pMatSky->setBaseColor(float4(0.4f, 0.6f, 1.f, 1.f));
    pMatSky->setDoubleSided(true);

    auto pMatOcean = StandardMaterial::create(getDevice(), "Ocean");
    pMatOcean->setBaseColor(float4(0.05f, 0.2f, 0.35f, 1.f));
    pMatOcean->setRoughness(0.15f);
    pMatOcean->setDoubleSided(true);

    auto pMatCube = StandardMaterial::create(getDevice(), "MorphCube");
    pMatCube->setBaseColor(float4(0.9f, 0.88f, 0.82f, 1.f));
    pMatCube->setRoughness(0.35f);
    pMatCube->setDoubleSided(true);

    auto pMatIsland = StandardMaterial::create(getDevice(), "Island");
    pMatIsland->setBaseColor(float4(0.4f, 0.48f, 0.28f, 1.f));
    pMatIsland->setRoughness(0.85f);
    pMatIsland->setDoubleSided(true);

    auto pMatLand = StandardMaterial::create(getDevice(), "Land");
    pMatLand->setBaseColor(float4(0.35f, 0.42f, 0.22f, 1.f));
    pMatLand->setRoughness(0.9f);
    pMatLand->setDoubleSided(true);

    MeshID skyID = builder.addTriangleMesh(TriangleMesh::createSphere(90.f, 48, 24), pMatSky);
    MeshID oceanID = builder.addTriangleMesh(createOceanGrid(96, 120.f), pMatOcean);
    MeshID morphID = builder.addTriangleMesh(TriangleMesh::createCube(float3(1.f)), pMatCube);
    MeshID islandID = builder.addTriangleMesh(TriangleMesh::createQuad(float2(1.f)), pMatIsland);
    MeshID landID = builder.addTriangleMesh(TriangleMesh::createQuad(float2(1.f)), pMatLand);
    MeshID hillID = builder.addTriangleMesh(TriangleMesh::createCube(float3(1.f)), pMatLand);

    Transform skyXform;
    mSkyNode = builder.addNode(SceneBuilder::Node{"SkyDome", skyXform.getMatrix(), float4x4(), float4x4()});
    builder.addMeshInstance(mSkyNode, skyID);

    Transform oceanXform;
    oceanXform.setRotationEulerDeg(float3(-90.f, 0.f, 0.f));
    oceanXform.setTranslation(float3(0.f, -0.15f, 0.f));
    mOceanNode = builder.addNode(SceneBuilder::Node{"Ocean", oceanXform.getMatrix(), float4x4(), float4x4()});
    builder.addMeshInstance(mOceanNode, oceanID);

    // Lesson morph cube - analytic shader canvas in front of the camera
    mCubePos = float3(0.f, 2.15f, 0.f);
    mCubeRotDeg = float3(8.f, 22.f, -6.f);
    mCubeScale = float3(2.0f);
    {
        Transform cx;
        cx.setTranslation(mCubePos);
        cx.setRotationEulerDeg(mCubeRotDeg);
        cx.setScaling(mCubeScale);
        mMorphCubeNode = builder.addNode(SceneBuilder::Node{"MorphCube", cx.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(mMorphCubeNode, morphID);
    }

    // Island plane under the cube
    mIslandPos = float3(0.f, 0.08f, 0.f);
    mIslandRotDeg = float3(-90.f, 0.f, 0.f);
    mIslandScale = float3(28.f, 28.f, 1.f);
    mIslandRadius = 14.f;
    {
        Transform ix;
        ix.setTranslation(mIslandPos);
        ix.setRotationEulerDeg(mIslandRotDeg);
        ix.setScaling(mIslandScale);
        mIslandNode = builder.addNode(SceneBuilder::Node{"Island", ix.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(mIslandNode, islandID);
    }

    // Distant land / hills - horizon silhouette beyond the water
    mLandNodes.clear();
    auto addLandFlat = [&](const char* name, float3 pos, float2 scaleXZ, float yawDeg = 0.f)
    {
        Transform lx;
        lx.setTranslation(pos);
        lx.setRotationEulerDeg(float3(-90.f, yawDeg, 0.f));
        lx.setScaling(float3(scaleXZ.x, scaleXZ.y, 1.f));
        NodeID n = builder.addNode(SceneBuilder::Node{name, lx.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, landID);
        mLandNodes.push_back(n);
        return n;
    };
    auto addHill = [&](const char* name, float3 pos, float3 scale)
    {
        Transform hx;
        hx.setTranslation(pos);
        hx.setScaling(scale);
        NodeID n = builder.addNode(SceneBuilder::Node{name, hx.getMatrix(), float4x4(), float4x4()});
        builder.addMeshInstance(n, hillID);
        mLandNodes.push_back(n);
        return n;
    };
    addLandFlat("LandDistant", float3(0.f, 0.4f, -82.f), float2(160.f, 60.f));
    addLandFlat("LandFarWest", float3(-70.f, 0.25f, -55.f), float2(50.f, 70.f), 18.f);
    addLandFlat("LandFarEast", float3(72.f, 0.25f, -50.f), float2(48.f, 65.f), -15.f);
    addHill("HillA", float3(-22.f, 4.5f, -72.f), float3(18.f, 9.f, 14.f));
    addHill("HillB", float3(8.f, 6.2f, -85.f), float3(24.f, 12.f, 18.f));
    addHill("HillC", float3(32.f, 3.8f, -68.f), float3(14.f, 7.f, 12.f));
    addHill("HillD", float3(-45.f, 5.0f, -90.f), float3(20.f, 10.f, 16.f));

    // Lesson bank - skippable looks on the cube (no walk-to-beacon)
    mStations = {
        {"bos/00_hello",
         "Hello UV",
         "UV lesson math on the morph cube - analytic faces you can orbit.",
         "Try: [ ] bank looks and watch the cube faces change.",
         "labs/book_of_shaders/shaders/00_hello.slang"},
        {"slang_playground/sp03_ocean",
         "Ocean world",
         "sp03 waves frame the island; the cube mirrors the water look.",
         "Try: orbit out - sky, ocean, distant shore, cube on the island.",
         "labs/slang_playground/shaders/sp03_ocean.slang"},
        {"bos/02_shaping",
         "Shaping / plasma",
         "Shaping functions become the cube's energy - sin/cos plasma on every face.",
         "Try: bank with ] and compare to UV.",
         "labs/book_of_shaders/shaders/02_shaping.slang"},
        {"slang_playground/sp02_circle",
         "Circle / polar",
         "Polar distance fields on the morph cube - a playground circle lifted into 3D.",
         "Try: RMB orbit; the ring stays in UV space on each face.",
         "labs/slang_playground/shaders/sp02_circle.slang"},
        {"slang_playground/sp06_gsplat2d",
         "Gaussian network",
         "3D sibling of the 2D splatter - a parameterizable Gaussian mixture on the cube (island tint too).",
         "Try: F1 -> Morph Cube / Environment knobs for count, sigma, colors, layer depth.",
         "labs/slang_playground/shaders/sp06_gsplat2d.slang"},
    };

    mActiveLesson = 0;
    applyActiveLessonLook();

    // Orbit looking at the cube on the island
    mCamYaw = 0.18f;
    mCamPitch = 0.28f;
    mCamDist = 10.5f;

    auto pCam = Camera::create("VernacularCam");
    pCam->setPosition(float3(0.f, 4.f, 12.f));
    pCam->setTarget(mCubePos);
    pCam->setUpVector(float3(0.f, 1.f, 0.f));
    pCam->setFocalLength(28.f);
    builder.addCamera(pCam);
    builder.setSelectedCamera(pCam);

    auto pKey = DistantLight::create("SunKey");
    pKey->setWorldDirection(float3(0.35f, -0.75f, -0.4f));
    pKey->setIntensity(float3(6.f, 5.4f, 4.2f));
    pKey->setAngle(0.08f);
    builder.addLight(pKey);

    mpScene = builder.getScene();
    mpCamera = mpScene->getCamera();
    mpScene->setCameraControlsEnabled(false);
    mpScene->setCameraSpeed(4.f);

    float radius = mpScene->getSceneBounds().radius();
    mpCamera->setDepthRange(0.1f, std::max(250.f, radius * 2.f));
    if (pTargetFbo)
        mpCamera->setAspectRatio(float(pTargetFbo->getWidth()) / float(pTargetFbo->getHeight()));

    createRasterPass();
    rebuildSceneObjects();
    updateOrbitCamera();
    mStatusMsg = "Studio | [ ] lessons | J/M folds | RMB orbit";
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

const char* VernacularViewport::kindLabel(SceneObjKind k) const
{
    switch (k)
    {
    case SceneObjKind::Environment:
        return "Environment";
    case SceneObjKind::SkyDome:
        return "Sky";
    case SceneObjKind::Ocean:
        return "Ocean";
    case SceneObjKind::MorphCube:
        return "Morph Cube";
    case SceneObjKind::Island:
        return "Island";
    case SceneObjKind::Land:
        return "Land";
    }
    return "Object";
}

void VernacularViewport::applyActiveLessonLook()
{
    if (mStations.empty())
    {
        mLessonLook = 0;
        loadActiveLessonCode();
        return;
    }
    mActiveLesson = std::clamp(mActiveLesson, 0, (int)mStations.size() - 1);
    const std::string& id = mStations[mActiveLesson].curriculumId;
    if (id.find("gsplat") != std::string::npos || id.find("gaussian") != std::string::npos)
        mLessonLook = 4; // 3D Gaussian network
    else if (id.find("ocean") != std::string::npos)
        mLessonLook = 1;
    else if (id.find("shaping") != std::string::npos)
        mLessonLook = 2;
    else if (id.find("circle") != std::string::npos)
        mLessonLook = 3;
    else
        mLessonLook = 0;
    mStatusMsg = std::string("Lesson: ") + mStations[mActiveLesson].title;
    loadActiveLessonCode();
}

void VernacularViewport::loadActiveLessonCode()
{
    mLessonCode.clear();
    mLessonCodePath.clear();
    mLessonCodeDirty = true;

    if (mStations.empty())
    {
        mLessonCode = "// No lessons loaded.\n";
        return;
    }

    mActiveLesson = std::clamp(mActiveLesson, 0, (int)mStations.size() - 1);
    const LessonStation& st = mStations[mActiveLesson];
    std::ostringstream header;
    header << "// " << st.title << "  (" << st.curriculumId << ")\n";
    header << "// " << st.blurb3d << "\n";
    header << "// Tip: " << st.tip << "\n";
    header << "// Look id " << mLessonLook << " paints the morph cube (analytic).\n\n";

    if (st.shaderRel.empty() || mRepoRoot.empty())
    {
        mLessonCode = header.str() + "// Curriculum shader path unavailable - open with L for 2D live.\n";
        return;
    }

    std::filesystem::path path = mRepoRoot / st.shaderRel;
    mLessonCodePath = path.generic_string();
    if (!std::filesystem::exists(path))
    {
        mLessonCode = header.str() + "// Missing file: " + mLessonCodePath + "\n";
        return;
    }

    std::ifstream in(path, std::ios::in | std::ios::binary);
    if (!in)
    {
        mLessonCode = header.str() + "// Failed to read: " + mLessonCodePath + "\n";
        return;
    }

    std::ostringstream body;
    body << in.rdbuf();
    std::string src = body.str();
    constexpr size_t kMaxBody = kLessonCodeBufSize - 1024;
    if (src.size() > kMaxBody)
    {
        src.resize(kMaxBody);
        src += "\n\n// … truncated for in-viewport panel …\n";
    }
    mLessonCode = header.str() + src;
}

void VernacularViewport::bankLesson(int delta)
{
    if (mStations.empty())
        return;
    int n = (int)mStations.size();
    mActiveLesson = (mActiveLesson + delta) % n;
    if (mActiveLesson < 0)
        mActiveLesson += n;
    applyActiveLessonLook();
}

void VernacularViewport::rebuildSceneObjects()
{
    mObjects.clear();

    {
        SceneObject env;
        env.name = "Environment";
        env.kind = SceneObjKind::Environment;
        mObjects.push_back(env);
    }
    {
        SceneObject sky;
        sky.name = "Sky Dome";
        sky.kind = SceneObjKind::SkyDome;
        sky.node = mSkyNode;
        mObjects.push_back(sky);
    }
    {
        SceneObject ocean;
        ocean.name = "Ocean";
        ocean.kind = SceneObjKind::Ocean;
        ocean.node = mOceanNode;
        ocean.position = float3(0.f, -0.15f, 0.f);
        ocean.rotationDeg = float3(-90.f, 0.f, 0.f);
        ocean.scale = float3(1);
        mObjects.push_back(ocean);
    }
    {
        SceneObject cube;
        cube.name = "Morph Cube";
        cube.kind = SceneObjKind::MorphCube;
        cube.node = mMorphCubeNode;
        cube.position = mCubePos;
        cube.rotationDeg = mCubeRotDeg;
        cube.scale = mCubeScale;
        mObjects.push_back(cube);
    }
    {
        SceneObject island;
        island.name = "Island";
        island.kind = SceneObjKind::Island;
        island.node = mIslandNode;
        island.position = mIslandPos;
        island.rotationDeg = mIslandRotDeg;
        island.scale = mIslandScale;
        mObjects.push_back(island);
    }

    static const char* kLandNames[] = {
        "LandDistant", "LandFarWest", "LandFarEast", "HillA", "HillB", "HillC", "HillD",
    };
    for (int i = 0; i < (int)mLandNodes.size(); ++i)
    {
        SceneObject land;
        land.name = (i < 7) ? kLandNames[i] : ("Land_" + std::to_string(i));
        land.kind = SceneObjKind::Land;
        land.node = mLandNodes[i];
        if (i < 3)
        {
            const float3 kPos[] = {
                float3(0.f, 0.4f, -82.f),
                float3(-70.f, 0.25f, -55.f),
                float3(72.f, 0.25f, -50.f),
            };
            const float3 kScale[] = {
                float3(160.f, 60.f, 1.f),
                float3(50.f, 70.f, 1.f),
                float3(48.f, 65.f, 1.f),
            };
            const float3 kRot[] = {
                float3(-90.f, 0.f, 0.f),
                float3(-90.f, 18.f, 0.f),
                float3(-90.f, -15.f, 0.f),
            };
            land.position = kPos[i];
            land.rotationDeg = kRot[i];
            land.scale = kScale[i];
        }
        else
        {
            const float3 kPos[] = {
                float3(-22.f, 4.5f, -72.f),
                float3(8.f, 6.2f, -85.f),
                float3(32.f, 3.8f, -68.f),
                float3(-45.f, 5.0f, -90.f),
            };
            const float3 kScale[] = {
                float3(18.f, 9.f, 14.f),
                float3(24.f, 12.f, 18.f),
                float3(14.f, 7.f, 12.f),
                float3(20.f, 10.f, 16.f),
            };
            int h = i - 3;
            land.position = kPos[h];
            land.scale = kScale[h];
        }
        mObjects.push_back(land);
    }

    // Prefer morph cube selected
    mSelected = 3;
}

void VernacularViewport::applySceneTransforms()
{
    if (!mpScene)
        return;

    for (auto& o : mObjects)
    {
        if (o.kind == SceneObjKind::MorphCube)
        {
            o.position = mCubePos;
            o.rotationDeg = mCubeRotDeg;
            o.scale = mCubeScale;
        }
        if (o.kind == SceneObjKind::Island)
        {
            o.position = mIslandPos;
            o.rotationDeg = mIslandRotDeg;
            o.scale = mIslandScale;
        }
    }

    for (const auto& o : mObjects)
    {
        if (o.node == NodeID::Invalid())
            continue;

        float3 s = effectiveScale(o.active, o.scale);
        if (o.kind == SceneObjKind::MorphCube)
        {
            float3 rot = mCubeRotDeg + float3(0.f, mTime * 8.f, 0.f);
            float3 sc = mCubeScale * (1.f + 0.03f * mMorph * std::sin(mTime * 1.7f));
            sc = effectiveScale(o.active, sc);
            mpScene->updateNodeTransform(uint32_t(o.node.get()), trsEuler(mCubePos, rot, sc));
        }
        else if (o.kind == SceneObjKind::Island)
        {
            mpScene->updateNodeTransform(uint32_t(o.node.get()), trsEuler(mIslandPos, mIslandRotDeg, s));
        }
        else if (o.kind == SceneObjKind::SkyDome || o.kind == SceneObjKind::Ocean || o.kind == SceneObjKind::Land)
        {
            mpScene->updateNodeTransform(uint32_t(o.node.get()), trsEuler(o.position, o.rotationDeg, s));
        }
    }
}

void VernacularViewport::nudgeSelected(float3 deltaPos, float3 deltaRotDeg, float3 deltaScale)
{
    if (mSelected < 0 || mSelected >= (int)mObjects.size())
        return;
    auto& o = mObjects[mSelected];
    if (o.kind == SceneObjKind::Environment)
        return;

    switch (mTool)
    {
    case TransformTool::Move:
        o.position += deltaPos;
        break;
    case TransformTool::Rotate:
        o.rotationDeg += deltaRotDeg;
        break;
    case TransformTool::Scale:
        o.scale += deltaScale;
        o.scale = float3(std::max(0.01f, o.scale.x), std::max(0.01f, o.scale.y), std::max(0.01f, o.scale.z));
        break;
    }

    if (o.kind == SceneObjKind::MorphCube)
    {
        mCubePos = o.position;
        mCubeRotDeg = o.rotationDeg;
        mCubeScale = o.scale;
    }
    if (o.kind == SceneObjKind::Island)
    {
        mIslandPos = o.position;
        mIslandRotDeg = o.rotationDeg;
        mIslandScale = o.scale;
        mIslandRadius = 0.5f * std::min(mIslandScale.x, mIslandScale.y);
    }
}

void VernacularViewport::drawHierarchy(Gui::Window& win)
{
    win.text("Scene");
    win.separator();
    for (int i = 0; i < (int)mObjects.size(); ++i)
    {
        const auto& o = mObjects[i];
        std::string label;
        if (i == mSelected)
            label += "> ";
        label += o.name;
        if (!o.active)
            label += " (off)";
        if (win.button(label.c_str()))
            mSelected = i;
    }
    win.separator();
    win.text("1 Move  2 Rotate  3 Scale");
    win.text("Arrows nudge | [ ] lessons");
}

void VernacularViewport::drawInspector(Gui::Window& win)
{
    Gui::RadioButtonGroup tools = {
        {0, "Move", false},
        {1, "Rotate", true},
        {2, "Scale", true},
    };
    uint32_t toolId = (uint32_t)mTool;
    if (win.radioButtons(tools, toolId))
        mTool = (TransformTool)toolId;

    win.var("Snap move", mSnapMove, 0.01f, 5.f, 0.01f);
    win.var("Snap rotate", mSnapRotate, 0.5f, 45.f, 0.5f);
    win.var("Snap scale", mSnapScale, 0.01f, 1.f, 0.01f);
    win.separator();

    if (mSelected < 0 || mSelected >= (int)mObjects.size())
    {
        win.text("Select an object in Hierarchy");
        return;
    }

    auto& o = mObjects[mSelected];
    win.textbox("Name", o.name);
    win.text(std::string("Type: ") + kindLabel(o.kind));
    win.checkbox("Active", o.active);

    if (o.kind != SceneObjKind::Environment)
    {
        win.separator();
        win.text("Transform");
        bool changed = false;
        changed |= win.var("Position", o.position, -200.f, 200.f, 0.01f);
        changed |= win.var("Rotation", o.rotationDeg, -360.f, 360.f, 0.1f);
        changed |= win.var("Scale", o.scale, 0.01f, 200.f, 0.01f);

        if (changed)
        {
            if (o.kind == SceneObjKind::MorphCube)
            {
                mCubePos = o.position;
                mCubeRotDeg = o.rotationDeg;
                mCubeScale = o.scale;
            }
            if (o.kind == SceneObjKind::Island)
            {
                mIslandPos = o.position;
                mIslandRotDeg = o.rotationDeg;
                mIslandScale = o.scale;
                mIslandRadius = 0.5f * std::min(mIslandScale.x, mIslandScale.y);
            }
        }

        win.separator();
        if (mTool == TransformTool::Move)
        {
            win.text("Nudge position");
            if (win.button("-X", true))
                nudgeSelected(float3(-mSnapMove, 0, 0), float3(0), float3(0));
            if (win.button("+X", true))
                nudgeSelected(float3(mSnapMove, 0, 0), float3(0), float3(0));
            if (win.button("-Y", true))
                nudgeSelected(float3(0, -mSnapMove, 0), float3(0), float3(0));
            if (win.button("+Y", true))
                nudgeSelected(float3(0, mSnapMove, 0), float3(0), float3(0));
            if (win.button("-Z", true))
                nudgeSelected(float3(0, 0, -mSnapMove), float3(0), float3(0));
            if (win.button("+Z", true))
                nudgeSelected(float3(0, 0, mSnapMove), float3(0), float3(0));
        }
        else if (mTool == TransformTool::Rotate)
        {
            win.text("Nudge rotation (deg)");
            if (win.button("-Yaw", true))
                nudgeSelected(float3(0), float3(0, -mSnapRotate, 0), float3(0));
            if (win.button("+Yaw", true))
                nudgeSelected(float3(0), float3(0, mSnapRotate, 0), float3(0));
            if (win.button("-Pitch", true))
                nudgeSelected(float3(0), float3(-mSnapRotate, 0, 0), float3(0));
            if (win.button("+Pitch", true))
                nudgeSelected(float3(0), float3(mSnapRotate, 0, 0), float3(0));
        }
        else
        {
            win.text("Nudge scale");
            if (win.button("-Size", true))
                nudgeSelected(float3(0), float3(0), float3(-mSnapScale, -mSnapScale, -mSnapScale));
            if (win.button("+Size", true))
                nudgeSelected(float3(0), float3(0), float3(mSnapScale, mSnapScale, mSnapScale));
        }
    }

    win.separator();
    if (o.kind == SceneObjKind::Environment)
    {
        win.text("Atmosphere");
        win.var("Sun elevation", mSunElev, 0.f, 1.f, 0.005f);
        win.var("Sun azimuth", mSunAzim, 0.f, 1.f, 0.005f);
        win.var("Cloud cover", mCloudCover, 0.f, 1.f, 0.01f);
        win.var("Fog density", mFogDensity, 0.f, 0.12f, 0.001f);
        win.var("Fog height", mFogHeight, 0.f, 2.f, 0.01f);
        win.var("Warm lights", mLightWarm, 0.f, 2.5f, 0.01f);
        win.var("Cool lights", mLightCool, 0.f, 2.5f, 0.01f);
        win.var("Exposure", mExposure, 0.3f, 2.5f, 0.01f);
        if (win.button("Preset (P)"))
            cycleLightPreset();
        win.checkbox("Animate", mAnimate);
        if (win.button("Julia (J)", true))
            mFoldMode = (mFoldMode == 1) ? 0u : 1u;
        if (win.button("Mandel (M)", true))
            triggerMandelbrotBurst();
    }
    else if (o.kind == SceneObjKind::MorphCube)
    {
        win.var("Morph amount", mMorph, 0.f, 1.5f, 0.01f);
        win.text("Lesson canvas - [ ] banks looks");
        if (!mStations.empty())
        {
            win.text(std::string("Active: ") + mStations[mActiveLesson].title);
            if (win.button("Prev [", true))
                bankLesson(-1);
            if (win.button("Next ]", true))
                bankLesson(1);
        }
        if (mLessonLook == 4)
        {
            win.separator();
            drawGaussNetworkControls(win);
        }
    }
    else if (o.kind == SceneObjKind::Island)
    {
        win.text("Shader island under the morph cube");
        win.var("Classify radius", mIslandRadius, 4.f, 40.f, 0.1f);
        if (mLessonLook == 4)
        {
            win.separator();
            win.text("Gaussian tint follows Morph Cube network knobs");
            drawGaussNetworkControls(win);
        }
    }
    else if (o.kind == SceneObjKind::Land)
    {
        win.text("Distant shore / hills");
    }

    if (!mStatusMsg.empty())
    {
        win.separator();
        win.text(mStatusMsg);
    }
    if (win.button("Optional 2D lessons (L)"))
        openLessonsWindow();
}

void VernacularViewport::drawLessonPanel(Gui::Window& win)
{
    if (mStations.empty())
    {
        win.text("No lessons loaded.");
        return;
    }

    mActiveLesson = std::clamp(mActiveLesson, 0, (int)mStations.size() - 1);
    const LessonStation& st = mStations[mActiveLesson];

    win.text(st.title);
    win.textWrapped(st.blurb3d);
    win.textWrapped(std::string("Try: ") + st.tip);
    win.separator();
    win.text(std::string("id: ") + st.curriculumId);
    win.text(std::string("cube look: ") + std::to_string(mLessonLook) + "  (0 UV | 1 ocean | 2 plasma | 3 circle | 4 gauss)");
    if (!mLessonCodePath.empty())
        win.textWrapped(mLessonCodePath);
    win.separator();

    if (win.button("Prev [", true))
        bankLesson(-1);
    if (win.button("Next ]", true))
        bankLesson(1);
    if (win.button("Reload", true))
        loadActiveLessonCode();
    if (win.button("2D live (L)"))
        openLessonsWindow(st.curriculumId);

    if (mLessonLook == 4)
    {
        win.separator();
        drawGaussNetworkControls(win);
    }

    win.separator();
    win.text("Curriculum shader (display / notes; cube uses analytic look)");
    if (mLessonCodeDirty)
    {
        std::memset(mLessonCodeBuf, 0, sizeof(mLessonCodeBuf));
        const size_t n = std::min(mLessonCode.size(), sizeof(mLessonCodeBuf) - 1);
        if (n > 0)
            std::memcpy(mLessonCodeBuf, mLessonCode.data(), n);
        mLessonCodeDirty = false;
    }
    if (win.textbox("##lesson_code", mLessonCodeBuf, sizeof(mLessonCodeBuf), 18))
        mLessonCode = mLessonCodeBuf;

    if (!mStatusMsg.empty())
    {
        win.separator();
        win.text(mStatusMsg);
    }
}

void VernacularViewport::triggerMandelbrotBurst()
{
    static const float2 kHot[] = {
        float2(-0.743643887037151f, 0.131825904205312f),
        float2(-0.77568377f, 0.13646737f),
        float2(-0.16f, 1.0405f),
        float2(-1.25066f, 0.02012f),
        float2(0.281717921647968f, 0.53020784769156f),
        float2(-0.748f, 0.1f),
        float2(-0.7453f, 0.1127f),
        float2(-0.235125f, 0.827215f),
    };
    mFoldSeed = mFoldSeed * 1664525u + 1013904223u;
    uint32_t idx = mFoldSeed % (uint32_t)(sizeof(kHot) / sizeof(kHot[0]));
    float jx = (float((mFoldSeed >> 3) & 1023u) / 1023.f - 0.5f) * 0.02f;
    float jy = (float((mFoldSeed >> 13) & 1023u) / 1023.f - 0.5f) * 0.02f;
    mMandelCenter = kHot[idx] + float2(jx, jy);
    mMandelLogZoom = 0.15f + 0.35f * (float((mFoldSeed >> 7) & 255u) / 255.f);
    mMandelZoomSpeed = 0.55f + 0.85f * (float((mFoldSeed >> 11) & 255u) / 255.f);
    mMandelActivity = 1.f;
    mFoldMode = 2;
    mFoldStrength = 1.f;
    mStatusMsg = "Mandelbrot burst";
}

void VernacularViewport::updateFoldAnimation()
{
    if (mFoldMode == 2 && mMandelActivity > 0.f)
    {
        float dt = 1.f / 60.f;
        mMandelLogZoom += mMandelZoomSpeed * dt * (0.65f + 1.8f * mMandelActivity);
        mMandelActivity = std::max(0.f, mMandelActivity - dt * 0.07f);
        float j = mMandelActivity * 0.00015f * std::exp(mMandelLogZoom * 0.15f);
        mMandelCenter.x += j * std::sin(mTime * 11.f);
        mMandelCenter.y += j * std::cos(mTime * 13.f);
        if (mMandelLogZoom > 14.f)
        {
            mMandelLogZoom = 1.f;
            triggerMandelbrotBurst();
        }
    }
    if (mFoldMode == 1)
    {
        mJuliaC.x = -0.75f + 0.12f * std::sin(mTime * 0.31f);
        mJuliaC.y = 0.18f + 0.10f * std::cos(mTime * 0.27f);
    }
}

void VernacularViewport::updateOrbitCamera()
{
    if (!mpCamera)
        return;
    float cp = std::cos(mCamPitch), sp = std::sin(mCamPitch);
    float cy = std::cos(mCamYaw), sy = std::sin(mCamYaw);
    float3 back = float3(sy * cp, sp, cy * cp);
    float3 target = mCubePos + float3(0.f, 0.15f, 0.f);
    float3 eye = target + back * mCamDist;
    mpCamera->setPosition(eye);
    mpCamera->setTarget(target);
    mpCamera->setUpVector(float3(0.f, 1.f, 0.f));
}

void VernacularViewport::drawGaussNetworkControls(Gui::Window& win)
{
    win.text("Gaussian network (3D | sp06 sibling)");
    int count = (int)mGaussCount;
    if (win.var("Blob count", count, 1, kGaussMax))
        mGaussCount = (uint32_t)count;
    win.var("Sigma", mGaussSigma, 0.04f, 0.9f, 0.005f);
    win.var("Amplitude", mGaussAmp, 0.1f, 3.f, 0.01f);
    win.var("Layer depth", mGaussLayerDepth, 0.f, 2.f, 0.01f);
    win.var("Mix / gain", mGaussMix, 0.f, 1.5f, 0.01f);
    win.var("Anim speed", mGaussAnim, 0.f, 2.f, 0.01f);
    win.var("Spread XYZ", mGaussSpread, 0.2f, 3.f, 0.01f);
    win.rgbColor("Color A", mGaussColA);
    win.rgbColor("Color B", mGaussColB);
    win.rgbColor("Color C", mGaussColC);
    if (win.button("Reset gauss defaults"))
    {
        mGaussCount = 6;
        mGaussSigma = 0.22f;
        mGaussAmp = 1.15f;
        mGaussLayerDepth = 0.55f;
        mGaussMix = 0.85f;
        mGaussAnim = 0.65f;
        mGaussColA = float3(0.95f, 0.35f, 0.2f);
        mGaussColB = float3(0.2f, 0.75f, 1.05f);
        mGaussColC = float3(0.95f, 0.9f, 0.25f);
        mGaussSpread = float3(1.f, 1.15f, 0.85f);
    }
}

void VernacularViewport::setPerFrameVars(const Fbo* /*pTargetFbo*/)
{
    auto var = mpRasterPass->getVars()->getRootVar();
    var["PerFrameCB"]["gTime"] = mTime;
    var["PerFrameCB"]["gFoldMode"] = mFoldMode;
    var["PerFrameCB"]["gFoldStrength"] = mFoldStrength;
    var["PerFrameCB"]["gMandelLogZoom"] = mMandelLogZoom;
    var["PerFrameCB"]["gJuliaC"] = mJuliaC;
    var["PerFrameCB"]["gMandelCenter"] = mMandelCenter;
    var["PerFrameCB"]["gMandelActivity"] = mMandelActivity;
    var["PerFrameCB"]["gSunElev"] = mSunElev;
    var["PerFrameCB"]["gSunAzim"] = mSunAzim;
    var["PerFrameCB"]["gCloudCover"] = mCloudCover;
    var["PerFrameCB"]["gFogDensity"] = mFogDensity;
    var["PerFrameCB"]["gFogHeight"] = mFogHeight;
    var["PerFrameCB"]["gLightWarm"] = mLightWarm;
    var["PerFrameCB"]["gLightCool"] = mLightCool;
    var["PerFrameCB"]["gExposure"] = mExposure;
    var["PerFrameCB"]["gCubePos"] = mCubePos;
    var["PerFrameCB"]["gCubeScale"] = length(mCubeScale) * 0.577f;
    var["PerFrameCB"]["gMorph"] = mMorph;
    var["PerFrameCB"]["gLessonLook"] = mLessonLook;
    var["PerFrameCB"]["gIslandCenter"] = mIslandPos;
    var["PerFrameCB"]["gIslandRadius"] = mIslandRadius;
    var["PerFrameCB"]["gGaussCount"] = mGaussCount;
    var["PerFrameCB"]["gGaussSigma"] = mGaussSigma;
    var["PerFrameCB"]["gGaussAmp"] = mGaussAmp;
    var["PerFrameCB"]["gGaussLayerDepth"] = mGaussLayerDepth;
    var["PerFrameCB"]["gGaussMix"] = mGaussMix;
    var["PerFrameCB"]["gGaussAnim"] = mGaussAnim;
    var["PerFrameCB"]["gGaussPad0"] = float2(0.f);
    var["PerFrameCB"]["gGaussColA"] = mGaussColA;
    var["PerFrameCB"]["gGaussPadA"] = 0.f;
    var["PerFrameCB"]["gGaussColB"] = mGaussColB;
    var["PerFrameCB"]["gGaussPadB"] = 0.f;
    var["PerFrameCB"]["gGaussColC"] = mGaussColC;
    var["PerFrameCB"]["gGaussPadC"] = 0.f;
    var["PerFrameCB"]["gGaussSpread"] = mGaussSpread;
    var["PerFrameCB"]["gGaussPadS"] = 0.f;
}

void VernacularViewport::onGuiRender(Gui* pGui)
{
    if (!mShowEditor && !mShowLessonPanel)
        return;

    if (mShowEditor)
    {
        Gui::Window hierarchy(pGui, "Hierarchy", {260, 420}, {12, 12});
        drawHierarchy(hierarchy);

        Gui::Window inspector(pGui, "Inspector", {340, 520}, {280, 12});
        drawInspector(inspector);
    }

    if (mShowLessonPanel)
    {
        Gui::Window lesson(pGui, "Lesson", {460, 620}, {640, 12});
        drawLessonPanel(lesson);
    }
}

void VernacularViewport::onFrameRender(RenderContext* pRenderContext, const ref<Fbo>& pTargetFbo)
{
    pRenderContext->clearFbo(pTargetFbo.get(), kClearColor, 1.0f, 0, FboAttachmentType::All);

    float dt = float(getFrameRate().getLastFrameTime());
    if (dt <= 0.f || dt > 0.1f)
        dt = 1.f / 60.f;
    (void)dt;

    if (mAnimate)
        mTime = float(getGlobalClock().getTime());
    applySceneTransforms();
    updateOrbitCamera();
    updateFoldAnimation();

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

    if (!mStations.empty())
    {
        const auto& active = mStations[mActiveLesson];
        std::string hud = std::string("Lesson: ") + active.title + "  |  [ ] skip  |  J/M folds  |  RMB orbit";
        getTextRenderer().render(pRenderContext, asciiForHud(hud), pTargetFbo, {16, 16});
        getTextRenderer().render(pRenderContext, asciiForHud(active.blurb3d), pTargetFbo, {16, 40});
        getTextRenderer().render(pRenderContext, asciiForHud(active.tip), pTargetFbo, {16, 64});
    }
    else
    {
        getTextRenderer().render(pRenderContext, "[ ] lessons  |  J/M folds  |  RMB orbit  |  F1 panels", pTargetFbo, {16, 16});
    }
}

bool VernacularViewport::onKeyEvent(const KeyboardEvent& keyEvent)
{
    if (keyEvent.type == KeyboardEvent::Type::KeyPressed)
    {
        if (keyEvent.key == Input::Key::F1)
        {
            mShowEditor = !mShowEditor;
            mStatusMsg = mShowEditor ? "Hierarchy/Inspector on" : "Panels off";
            return true;
        }
        if (keyEvent.key == Input::Key::F2)
        {
            mShowLessonPanel = !mShowLessonPanel;
            mStatusMsg = mShowLessonPanel ? "Lesson panel on" : "Lesson panel off";
            return true;
        }
        if (keyEvent.key == Input::Key::Key1)
        {
            mTool = TransformTool::Move;
            mStatusMsg = "Tool: Move";
            return true;
        }
        if (keyEvent.key == Input::Key::Key2)
        {
            mTool = TransformTool::Rotate;
            mStatusMsg = "Tool: Rotate";
            return true;
        }
        if (keyEvent.key == Input::Key::Key3)
        {
            mTool = TransformTool::Scale;
            mStatusMsg = "Tool: Scale";
            return true;
        }
        // Left/Right always bank lessons when panels are closed; nudge when editor is open
        if (keyEvent.key == Input::Key::Left)
        {
            if (mShowEditor)
            {
                if (mTool == TransformTool::Move)
                    nudgeSelected(float3(-mSnapMove, 0, 0), float3(0), float3(0));
                else if (mTool == TransformTool::Rotate)
                    nudgeSelected(float3(0), float3(0, -mSnapRotate, 0), float3(0));
                else
                    nudgeSelected(float3(0), float3(0), float3(-mSnapScale, -mSnapScale, -mSnapScale));
            }
            else
                bankLesson(-1);
            return true;
        }
        if (keyEvent.key == Input::Key::Right)
        {
            if (mShowEditor)
            {
                if (mTool == TransformTool::Move)
                    nudgeSelected(float3(mSnapMove, 0, 0), float3(0), float3(0));
                else if (mTool == TransformTool::Rotate)
                    nudgeSelected(float3(0), float3(0, mSnapRotate, 0), float3(0));
                else
                    nudgeSelected(float3(0), float3(0), float3(mSnapScale, mSnapScale, mSnapScale));
            }
            else
                bankLesson(1);
            return true;
        }
        if (mShowEditor && keyEvent.key == Input::Key::Up)
        {
            if (mTool == TransformTool::Move)
                nudgeSelected(float3(0, 0, mSnapMove), float3(0), float3(0));
            else if (mTool == TransformTool::Rotate)
                nudgeSelected(float3(0), float3(mSnapRotate, 0, 0), float3(0));
            else
                nudgeSelected(float3(0), float3(0), float3(mSnapScale, mSnapScale, mSnapScale));
            return true;
        }
        if (mShowEditor && keyEvent.key == Input::Key::Down)
        {
            if (mTool == TransformTool::Move)
                nudgeSelected(float3(0, 0, -mSnapMove), float3(0), float3(0));
            else if (mTool == TransformTool::Rotate)
                nudgeSelected(float3(0), float3(-mSnapRotate, 0, 0), float3(0));
            else
                nudgeSelected(float3(0), float3(0), float3(-mSnapScale, -mSnapScale, -mSnapScale));
            return true;
        }
        if (mShowEditor && keyEvent.key == Input::Key::PageUp)
        {
            if (mTool == TransformTool::Move)
                nudgeSelected(float3(0, mSnapMove, 0), float3(0), float3(0));
            return true;
        }
        if (mShowEditor && keyEvent.key == Input::Key::PageDown)
        {
            if (mTool == TransformTool::Move)
                nudgeSelected(float3(0, -mSnapMove, 0), float3(0), float3(0));
            return true;
        }
        if (keyEvent.key == Input::Key::LeftBracket)
        {
            bankLesson(-1);
            return true;
        }
        if (keyEvent.key == Input::Key::RightBracket)
        {
            bankLesson(1);
            return true;
        }
        if (keyEvent.key == Input::Key::L)
        {
            if (mActiveLesson >= 0 && mActiveLesson < (int)mStations.size())
                openLessonsWindow(mStations[mActiveLesson].curriculumId);
            else
                openLessonsWindow();
            return true;
        }
        if (keyEvent.key == Input::Key::P)
        {
            cycleLightPreset();
            return true;
        }
        if (keyEvent.key == Input::Key::J)
        {
            mFoldMode = (mFoldMode == 1) ? 0u : 1u;
            mStatusMsg = mFoldMode ? "Julia fold" : "Fold off";
            return true;
        }
        if (keyEvent.key == Input::Key::M)
        {
            triggerMandelbrotBurst();
            return true;
        }
        if (keyEvent.key == Input::Key::Key0)
        {
            mFoldMode = 0;
            mMandelActivity = 0.f;
            mStatusMsg = "Fold off";
            return true;
        }
    }
    return false;
}

bool VernacularViewport::onMouseEvent(const MouseEvent& mouseEvent)
{
    if (mouseEvent.type == MouseEvent::Type::ButtonDown && mouseEvent.button == Input::MouseButton::Right)
    {
        mOrbitDrag = true;
        mLastMouse = mouseEvent.pos;
        return true;
    }
    if (mouseEvent.type == MouseEvent::Type::ButtonUp && mouseEvent.button == Input::MouseButton::Right)
    {
        mOrbitDrag = false;
        return true;
    }
    if (mouseEvent.type == MouseEvent::Type::Move && mOrbitDrag)
    {
        float2 d = mouseEvent.pos - mLastMouse;
        mLastMouse = mouseEvent.pos;
        mCamYaw -= d.x * 0.01f;
        mCamPitch = std::clamp(mCamPitch + d.y * 0.01f, -0.05f, 1.35f);
        return true;
    }
    if (mouseEvent.type == MouseEvent::Type::Wheel)
    {
        mCamDist = std::clamp(mCamDist - mouseEvent.wheelDelta.y * 0.6f, 3.5f, 28.f);
        return true;
    }
    return false;
}

void VernacularViewport::onHotReload(HotReloadFlags reloaded)
{
    if (is_set(reloaded, HotReloadFlags::Program) && mpScene)
        createRasterPass();
}

int runMain(int /*argc*/, char** /*argv*/)
{
    SampleAppConfig config;
    config.windowDesc.title = "VERNACULAR - Abstract Studio";
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

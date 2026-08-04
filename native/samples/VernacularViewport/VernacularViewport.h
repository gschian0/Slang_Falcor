// VERNACULAR abstract studio — lesson cube on island, ocean/sky, orbit camera.
// Plan: docs/plans/vernacular-3d-lesson-world.md
#pragma once

#include "Falcor.h"
#include "Core/SampleApp.h"
#include "Core/Pass/RasterPass.h"

#include <array>
#include <string>
#include <vector>

using namespace Falcor;

class VernacularViewport : public SampleApp
{
public:
    VernacularViewport(const SampleAppConfig& config);
    ~VernacularViewport() override = default;

    void onLoad(RenderContext* pRenderContext) override;
    void onResize(uint32_t width, uint32_t height) override;
    void onFrameRender(RenderContext* pRenderContext, const ref<Fbo>& pTargetFbo) override;
    void onGuiRender(Gui* pGui) override;
    bool onKeyEvent(const KeyboardEvent& keyEvent) override;
    bool onMouseEvent(const MouseEvent& mouseEvent) override;
    void onHotReload(HotReloadFlags reloaded) override;

private:
    enum class SceneObjKind : uint32_t
    {
        Environment = 0,
        SkyDome,
        Ocean,
        MorphCube,
        Island,
        Land,
    };

    /// Unity-style transform tool (1/2/3 — Move / Rotate / Scale).
    enum class TransformTool : uint32_t
    {
        Move = 0,
        Rotate = 1,
        Scale = 2,
    };

    struct SceneObject
    {
        std::string name;
        SceneObjKind kind = SceneObjKind::Environment;
        NodeID node = NodeID::Invalid();
        float3 position = float3(0);
        float3 rotationDeg = float3(0);
        float3 scale = float3(1);
        bool active = true;
        int parent = -1;
    };

    struct LessonStation
    {
        std::string curriculumId;
        std::string title;
        std::string blurb3d;
        std::string tip;
        std::string shaderRel;
    };

    void buildVernacularScene(const Fbo* pTargetFbo);
    void rebuildSceneObjects();
    void createRasterPass();
    void setPerFrameVars(const Fbo* pTargetFbo);
    void discoverRepoPaths();
    void openLessonsWindow(const std::string& lessonSpec = {});
    void triggerMandelbrotBurst();
    void updateFoldAnimation();
    void cycleLightPreset();
    void updateOrbitCamera();
    void applySceneTransforms();
    void nudgeSelected(float3 deltaPos, float3 deltaRotDeg, float3 deltaScale);
    void bankLesson(int delta);
    void applyActiveLessonLook();
    void loadActiveLessonCode();
    void drawHierarchy(Gui::Window& win);
    void drawInspector(Gui::Window& win);
    void drawLessonPanel(Gui::Window& win);
    void drawGaussNetworkControls(Gui::Window& win);
    const char* kindLabel(SceneObjKind k) const;

    ref<Scene> mpScene;
    ref<Camera> mpCamera;
    ref<RasterPass> mpRasterPass;

    float mTime = 0.f;
    bool mAnimate = true;
    bool mShowEditor = false; // Hierarchy + Inspector (F1) — off by default
    bool mShowLessonPanel = false; // F2

    // Atmosphere
    float mSunElev = 0.55f;
    float mSunAzim = 0.18f;
    float mCloudCover = 0.25f;
    float mFogDensity = 0.008f;
    float mFogHeight = 0.4f;
    float mLightWarm = 0.75f;
    float mLightCool = 0.45f;
    float mExposure = 1.05f;
    uint32_t mLightPreset = 0;

    // Orbit camera around the morph cube
    float mCamYaw = 0.15f;
    float mCamPitch = 0.32f;
    float mCamDist = 9.5f;
    bool mOrbitDrag = false;
    float2 mLastMouse = float2(0, 0);

    NodeID mSkyNode = NodeID::Invalid();
    NodeID mOceanNode = NodeID::Invalid();
    NodeID mMorphCubeNode = NodeID::Invalid();
    NodeID mIslandNode = NodeID::Invalid();
    std::vector<NodeID> mLandNodes;

    // Morph cube — lesson canvas
    float3 mCubePos = float3(0.f, 2.15f, 0.f);
    float3 mCubeRotDeg = float3(8.f, 22.f, -6.f);
    float3 mCubeScale = float3(2.0f);
    float mMorph = 0.65f;

    // Island under the cube
    float3 mIslandPos = float3(0.f, 0.08f, 0.f);
    float3 mIslandRotDeg = float3(-90.f, 0.f, 0.f);
    float3 mIslandScale = float3(28.f, 28.f, 1.f);
    float mIslandRadius = 14.f;

    // 3D Gaussian network (sp06 / NG03 big sibling) — analytic mixture on the cube
    static constexpr int kGaussMax = 8;
    uint32_t mGaussCount = 6;
    float mGaussSigma = 0.22f;
    float mGaussAmp = 1.15f;
    float mGaussLayerDepth = 0.55f;
    float mGaussMix = 0.85f;
    float mGaussAnim = 0.65f;
    float3 mGaussColA = float3(0.95f, 0.35f, 0.2f);
    float3 mGaussColB = float3(0.2f, 0.75f, 1.05f);
    float3 mGaussColC = float3(0.95f, 0.9f, 0.25f);
    float3 mGaussSpread = float3(1.f, 1.15f, 0.85f); // anisotropic sigma scales

    std::vector<SceneObject> mObjects;
    int mSelected = -1;
    TransformTool mTool = TransformTool::Move;
    float mSnapMove = 0.25f;
    float mSnapRotate = 5.f;
    float mSnapScale = 0.05f;

    std::vector<LessonStation> mStations;
    int mActiveLesson = 0;
    uint32_t mLessonLook = 0;
    std::string mLessonCode;
    std::string mLessonCodePath;
    bool mLessonCodeDirty = true;
    static constexpr size_t kLessonCodeBufSize = 49152;
    char mLessonCodeBuf[kLessonCodeBufSize]{};

    uint32_t mFoldMode = 0;
    float mFoldStrength = 1.f;
    float2 mJuliaC = float2(-0.8f, 0.156f);
    float2 mMandelCenter = float2(-0.743643887037151f, 0.131825904205312f);
    float mMandelLogZoom = 0.f;
    float mMandelZoomSpeed = 0.f;
    float mMandelActivity = 0.f;
    uint32_t mFoldSeed = 1;

    std::filesystem::path mRepoRoot;
    std::filesystem::path mVenvPython;
    std::string mStatusMsg;
};

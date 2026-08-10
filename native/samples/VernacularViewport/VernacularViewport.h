// VERNACULAR — Temple of Secret Knowledge (Iteration 3+).
// Vibration Modes of Cube = Iteration 2, pinned behind ShowMode::VibrationModes.
// Iteration 4: Orbit/Fly — Iteration 5: spatial audio — Iteration 6: square plane / UV / light / water.
// Iteration 7: cheap upscale ladder + shader school window + compute boids.
#pragma once

#include "Falcor.h"
#include "Core/SampleApp.h"
#include "Core/Pass/RasterPass.h"
#include "Core/Pass/ComputePass.h"
#include "Core/Pass/FullScreenPass.h"
#include "VernacularSoundscape.h"

#include <filesystem>
#include <memory>
#include <string>
#include <vector>

using namespace Falcor;

class VernacularViewport : public SampleApp
{
public:
    VernacularViewport(const SampleAppConfig& config);
    ~VernacularViewport() override;

    void onLoad(RenderContext* pRenderContext) override;
    void onShutdown() override;
    void onResize(uint32_t width, uint32_t height) override;
    void onFrameRender(RenderContext* pRenderContext, const ref<Fbo>& pTargetFbo) override;
    void onGuiRender(Gui* pGui) override;
    bool onKeyEvent(const KeyboardEvent& keyEvent) override;
    bool onMouseEvent(const MouseEvent& mouseEvent) override;
    void onHotReload(HotReloadFlags reloaded) override;

    enum class ShowMode : uint32_t
    {
        TempleSchool = 0,
        VibrationModes = 1,
    };

    // Familiar DCC / Falcor-style movement only (no exotic schemes).
    enum class MoveMode : uint32_t
    {
        Orbit = 0, // RMB drag orbit + wheel zoom (default)
        Fly = 1,   // WASD + QE + RMB look
    };

    // Iteration 6 — shades banked look with the same sun as sky / ocean.
    enum class LightMode : uint32_t
    {
        Unlit = 0,
        Lambert = 1,
        Blinn = 2,
        Physical = 3,
    };

    // Iteration 7 — render low, reconstruct high. DLSS is NGX (greyed in SampleApp).
    enum class UpscaleMode : uint32_t
    {
        Off = 0,
        InternalScale = 1,
        TAA = 2,
        DLSS = 3, // unavailable — see mDlssWhy
    };

    struct ChapterStation
    {
        const char* title;
        const char* stage;
        const char* blurb;
        const char* tip;
    };

private:
    void buildVernacularScene(const Fbo* pTargetFbo);
    void buildTempleScene(SceneBuilder& builder, const Fbo* pTargetFbo);
    void buildVibrationScene(SceneBuilder& builder, const Fbo* pTargetFbo);
    void createRasterPass();
    void setPerFrameVars(const Fbo* pTargetFbo);
    void updateCamera(float dt);
    void resolveMaterialIds();
    uint32_t materialIdByName(const std::string& name) const;
    const ChapterStation& activeStation() const;
    const char* chapterName() const;
    const char* moveModeName() const;
    const char* lightModeName() const;
    const char* upscaleModeName() const;
    void captureCubeRotation();
    void cycleLightMode();
    void cycleUpscaleMode();
    void addCubeInstance(SceneBuilder& builder, MeshID meshID, const float3& pos, float scale, const std::string& name);
    void switchShowMode(ShowMode mode);
    void setMoveMode(MoveMode mode);
    void clearFlyKeys();
    void syncOrbitFromEye();
    float3 lookDirFromYawPitch() const;
    void initAudio();
    void shutdownAudio();
    void updateSoundscape(float dt);

    // Iteration 7
    void loadSchoolPaths();
    void syncLessonSourcesIfNeeded(bool force);
    void openSchoolEditor();
    void ensureUpscaleTargets(uint32_t displayW, uint32_t displayH);
    void createSchoolPasses();
    void initBoids();
    void dispatchBoids(RenderContext* pRenderContext, float dt);
    void drawBoids(RenderContext* pRenderContext, const ref<Fbo>& pFbo);
    void applyUpscale(RenderContext* pRenderContext, const ref<Fbo>& pSceneFbo, const ref<Fbo>& pTargetFbo);
    bool usesInternalTarget() const;
    float internalScale() const;
    const char* dlssWhy() const;

    ref<Scene> mpScene;
    ref<Camera> mpCamera;
    ref<RasterPass> mpRasterPass;

    ShowMode mShowMode = ShowMode::TempleSchool;
    MoveMode mMoveMode = MoveMode::Orbit;
    LightMode mLightMode = LightMode::Unlit;
    UpscaleMode mUpscaleMode = UpscaleMode::Off;

    static constexpr uint32_t kChapterCount = 16;
    uint32_t mChapter = 0;

    float mTime = 0.f;
    float mVibeAmp = 0.22f;
    bool mAnimate = true;
    bool mVertexWaves = true;
    bool mShowControls = false; // F1
    bool mShowStation = false;  // F2

    // Env (temple)
    float mSunElev = 0.38f;
    float mSunAzim = 0.22f;
    float mCloudCover = 0.42f;
    float mFogDensity = 0.018f;
    float mFogHeight = 0.35f;
    float mExposure = 1.05f;
    float mSkyIntensity = 1.0f;

    // Water
    float mWaterScale = 0.55f;
    float mWaterChop = 0.85f;
    float mWaterAbsorb = 0.65f;
    float3 mWaterColor = float3(0.04f, 0.09f, 0.18f);

    // Orbit / fly — mouse pos is Falcor-normalized [0,1]; gains are radians per full-width drag.
    float3 mOrbitTarget = float3(0.f, 2.0f, 0.f);
    float mCamYaw = 0.12f;
    float mCamPitch = 0.22f;
    float mCamDist = 11.0f;
    bool mLookDrag = false;
    float2 mLastMouse = float2(0, 0);
    float3 mFlyPos = float3(0.f, 3.2f, 11.f);
    float mFlySpeed = 6.f;
    bool mKeyW = false, mKeyA = false, mKeyS = false, mKeyD = false, mKeyQ = false, mKeyE = false;
    bool mKeyShift = false;
    double mLastFrameTime = 0.0;

    uint32_t mMatFloor = 0xffffffffu;
    uint32_t mMatCube = 0xffffffffu;
    uint32_t mMatLetter = 0xffffffffu;
    uint32_t mMatSky = 0xffffffffu;
    uint32_t mMatOcean = 0xffffffffu;
    uint32_t mMatLand = 0xffffffffu;
    uint32_t mMatCanvas = 0xffffffffu;

    // Iteration 6 — square plane + canvas layout (shared with ocean reflection CB).
    float mPlaneSize = 3.4f;
    float3 mPlaneCenter = float3(0.f, 2.05f, 0.f);
    float3 mSphereCenter = float3(-5.2f, 1.9f, 1.1f);
    float mSphereRadius = 0.85f;
    float3 mCubeCenter = float3(5.2f, 1.9f, 1.1f);
    float mCubeSize = 1.45f;
    float3 mCubeEulerDeg = float3(8.f, 28.f, -6.f);
    float3 mCubeRot0 = float3(1.f, 0.f, 0.f);
    float3 mCubeRot1 = float3(0.f, 1.f, 0.f);
    float3 mCubeRot2 = float3(0.f, 0.f, 1.f);

    // Iteration 5 — spatial engine (camera = listener). Mute with M.
    VernacularSoundscape mSoundscape;
    bool mAudioMute = false;
    bool mAudioDoppler = true;
    float mAudioMasterGain = 1.f;
    float3 mAudioLastEye = float3(0.f);
    bool mAudioHaveLastEye = false;

    // Iteration 7 — internal scale / TAA / blit
    uint32_t mScaleIndex = 1; // 0=0.50 1=0.67 2=1.0 (used when not Off)
    bool mBicubicBlit = true;
    ref<Fbo> mpSceneFbo;
    ref<Fbo> mpMvecFbo;
    ref<Fbo> mpTaaFbo;
    ref<Texture> mpPrevColor;
    ref<FullScreenPass> mpMvecPass;
    ref<FullScreenPass> mpTaaPass;
    ref<FullScreenPass> mpBlitPass;
    ref<Sampler> mpLinearSampler;
    float4x4 mPrevViewProj = float4x4::identity();
    bool mHavePrevViewProj = false;
    bool mResetTaa = true;
    uint32_t mInternalW = 0;
    uint32_t mInternalH = 0;
    uint32_t mDisplayW = 0;
    uint32_t mDisplayH = 0;

    // Iteration 7 — compute boids
    static constexpr uint32_t kBoidCount = 128;
    bool mBoidsEnabled = false;
    ref<ComputePass> mpBoidsCs;
    ref<RasterPass> mpBoidPass;
    ref<Buffer> mpBoids[2];
    uint32_t mBoidSrc = 0;
    float3 mBoidOrigin = float3(0.f, 7.5f, -14.f);
    float mBoidRadius = 16.f;

    // School editor + lesson sync
    std::filesystem::path mRepoLessons;
    std::filesystem::path mShaderLessons;
    std::filesystem::path mRepoRoot;
    std::filesystem::path mPythonExe;
    std::filesystem::path mEditorCmd;
    std::string mDlssWhy;
    double mLastLessonPoll = 0.0;

    std::string mStatusMsg;
};

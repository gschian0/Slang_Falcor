// VERNACULAR — Temple of Secret Knowledge (Iteration 3+).
// Vibration Modes of Cube = Iteration 2, pinned behind ShowMode::VibrationModes.
// Iteration 4: Orbit/Fly movement fix — docs/plans/vernacular-viewport-iterations.md
#pragma once

#include "Falcor.h"
#include "Core/SampleApp.h"
#include "Core/Pass/RasterPass.h"

#include <atomic>
#include <memory>
#include <string>
#include <thread>
#include <vector>

using namespace Falcor;

class VernacularViewport : public SampleApp
{
public:
    VernacularViewport(const SampleAppConfig& config);
    ~VernacularViewport() override;

    void onLoad(RenderContext* pRenderContext) override;
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
    void addCubeInstance(SceneBuilder& builder, MeshID meshID, const float3& pos, float scale, const std::string& name);
    void switchShowMode(ShowMode mode);
    void setMoveMode(MoveMode mode);
    void clearFlyKeys();
    void syncOrbitFromEye();
    float3 lookDirFromYawPitch() const;
    void initAudio();
    void shutdownAudio();
    void updateAudioState();

    ref<Scene> mpScene;
    ref<Camera> mpCamera;
    ref<RasterPass> mpRasterPass;

    ShowMode mShowMode = ShowMode::TempleSchool;
    MoveMode mMoveMode = MoveMode::Orbit;

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

    // Delta-wave audio MVP (WASAPI) — Ch0 UV only; mute with M
    bool mAudioMute = false;
    bool mAudioOk = false;
    std::atomic<bool> mAudioRun{false};
    std::atomic<bool> mAudioActive{false}; // true when Ch0 + unmuted
    std::thread mAudioThread;
    std::string mAudioStatus = "audio off";

    std::string mStatusMsg;
};

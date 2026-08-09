// VERNACULAR — Iteration 5 spatial audio engine (host-side physics).
// Spherical omni sources + 1/r distance + stereo equal-power pan + Doppler.
// WASAPI shared-mode backend (Windows). Fail-soft: graphics never waits.
// Design: docs/plans/vernacular-viewport-spatial-audio.md
#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <thread>

class VernacularSoundscape
{
public:
    // --- Physics constants (world units treated as meters) ---
    static constexpr float kSpeedOfSound = 343.f;   // m/s
    static constexpr float kMinDistance = 1.5f;     // clamp singularity
    static constexpr float kRefDistance = 4.0f;     // unity spherical-spreading reference
    static constexpr float kMaxDistance = 36.f;     // silence beyond
    static constexpr float kFadeStart = 20.f;       // extra fade → 0 by kMaxDistance
    static constexpr float kDopplerRatioMin = 0.88f;
    static constexpr float kDopplerRatioMax = 1.15f; // keep orbit/fly musical, not cartoon
    static constexpr int kMaxSources = 8;
    static constexpr int kMaxPartials = 3;
    static constexpr int kBowlSlot = 0;
    static constexpr int kAtmosphereSlot = 1;
    static constexpr int kChirpSlot0 = 2; // optional bird hooks — reserved, unused this pass
    static constexpr int kChirpCount = 3;

    struct Vec3
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
    };

    enum class SourceKind : uint32_t
    {
        Bowl = 0,       // 2–3 singing-bowl / delta-wave sines
        Atmosphere = 1, // cheap filtered noise bed
        ChirpHook = 2,  // reserved point source (silent until filled)
    };

    struct Listener
    {
        Vec3 position;
        Vec3 forward;
        Vec3 up{0.f, 1.f, 0.f};
        Vec3 velocity; // world m/s (finite-diff from camera)
    };

    struct Source
    {
        bool enabled = false;
        SourceKind kind = SourceKind::Bowl;
        Vec3 position;
        Vec3 velocity; // 0 = static emitter
        float freqs[kMaxPartials] = {120.f, 122.f, 241.f};
        float amps[kMaxPartials] = {0.09f, 0.09f, 0.028f};
        float lookBoost = 1.f; // extra gain when looking at / near the source
    };

    struct SpatialResult
    {
        float distance = 0.f;
        float distanceGain = 0.f;
        float dopplerRatio = 1.f;
        float pan = 0.f; // -1 left .. +1 right
        float leftGain = 0.7071f;
        float rightGain = 0.7071f;
    };

    VernacularSoundscape() = default;
    ~VernacularSoundscape();

    VernacularSoundscape(const VernacularSoundscape&) = delete;
    VernacularSoundscape& operator=(const VernacularSoundscape&) = delete;

    // Fail-soft. Returns false if the device thread could not be launched.
    bool start();
    void stop();

    void setMuted(bool mute);
    void setMasterGain(float gain);
    void setDopplerEnabled(bool enabled);
    void setListener(const Listener& listener);
    void setSource(int slot, const Source& source);
    void clearSources();

    bool ok() const { return mDeviceOk.load(); }
    bool running() const { return mRun.load(); }
    std::string status() const;
    std::string debugLine() const; // main-thread snapshot (distance / doppler / pan)

    static float distanceGain(float dist);
    static float dopplerRatio(const Listener& listener, const Source& source);
    static SpatialResult evaluate(const Listener& listener, const Source& source, bool dopplerEnabled);

private:
    struct Snapshot
    {
        Listener listener;
        std::array<Source, kMaxSources> sources{};
        float masterGain = 1.f;
        bool mute = false;
        bool doppler = true;
    };

    void publish(const Snapshot& snap);
    Snapshot capture() const;
    void setStatus(const char* text);
    void audioThreadMain();

    mutable std::mutex mMutex;
    Snapshot mSnap;
    std::string mStatus = "audio off";

    std::atomic<bool> mRun{false};
    std::atomic<bool> mDeviceOk{false};
    std::thread mThread;
};

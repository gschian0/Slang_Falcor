// VERNACULAR — Iteration 5 spatial audio (WASAPI shared mix + host physics).
#include "VernacularSoundscape.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <sstream>

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#pragma comment(lib, "ole32.lib")
#endif

namespace
{
constexpr float kPi = 3.14159265358979323846f;
constexpr double kTwoPi = 6.28318530717958647692;

float length3(const VernacularSoundscape::Vec3& v)
{
    return std::sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
}

VernacularSoundscape::Vec3 sub3(const VernacularSoundscape::Vec3& a, const VernacularSoundscape::Vec3& b)
{
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}

float dot3(const VernacularSoundscape::Vec3& a, const VernacularSoundscape::Vec3& b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

VernacularSoundscape::Vec3 cross3(const VernacularSoundscape::Vec3& a, const VernacularSoundscape::Vec3& b)
{
    return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}

VernacularSoundscape::Vec3 normalize3(const VernacularSoundscape::Vec3& v, const VernacularSoundscape::Vec3& fallback)
{
    float len = length3(v);
    if (len < 1e-5f)
        return fallback;
    return {v.x / len, v.y / len, v.z / len};
}

#if defined(_WIN32)
bool mixIsFloat32(const WAVEFORMATEX* wfx)
{
    // Shared-mode mix is almost always IEEE float32 (WAVE_FORMAT_EXTENSIBLE).
    return wfx && wfx->wBitsPerSample == 32;
}

bool mixIsPcm16(const WAVEFORMATEX* wfx)
{
    return wfx && wfx->wBitsPerSample == 16;
}
#endif
} // namespace

float VernacularSoundscape::distanceGain(float dist)
{
    if (dist >= kMaxDistance)
        return 0.f;
    dist = std::max(dist, 0.f);
    const float spreading = std::clamp(kRefDistance / std::max(dist, kMinDistance), 0.f, 1.f);
    float fade = 1.f;
    if (dist > kFadeStart)
    {
        const float span = std::max(1e-3f, kMaxDistance - kFadeStart);
        fade = 1.f - (dist - kFadeStart) / span;
    }
    return spreading * std::clamp(fade, 0.f, 1.f);
}

float VernacularSoundscape::dopplerRatio(const Listener& listener, const Source& source)
{
    const Vec3 srcToLis = sub3(listener.position, source.position);
    const float dist = length3(srcToLis);
    if (dist < 1e-4f)
        return 1.f;

    // dir: source → listener. vL > 0 when listener moves toward source.
    // vS > 0 when source recedes from listener (classic acoustic signs).
    const Vec3 dir = {srcToLis.x / dist, srcToLis.y / dist, srcToLis.z / dist};
    const float vListenerRadial = -dot3(listener.velocity, dir);
    const float vSourceRadial = -dot3(source.velocity, dir);
    const float c = kSpeedOfSound;
    float num = c + vListenerRadial;
    float den = c + vSourceRadial;
    num = std::max(num, 8.f);
    den = std::max(den, 8.f);
    return std::clamp(num / den, kDopplerRatioMin, kDopplerRatioMax);
}

VernacularSoundscape::SpatialResult VernacularSoundscape::evaluate(const Listener& listener, const Source& source, bool dopplerEnabled)
{
    SpatialResult r;
    const Vec3 toSrc = sub3(source.position, listener.position);
    r.distance = length3(toSrc);
    r.distanceGain = distanceGain(r.distance);
    r.dopplerRatio = (dopplerEnabled && (source.kind == SourceKind::Bowl || source.kind == SourceKind::ChirpHook))
                         ? dopplerRatio(listener, source)
                         : 1.f;

    Vec3 forward = normalize3(listener.forward, {0.f, 0.f, -1.f});
    Vec3 up = normalize3(listener.up, {0.f, 1.f, 0.f});
    Vec3 right = cross3(forward, up);
    if (length3(right) < 1e-4f)
        right = cross3(forward, {0.f, 1.f, 0.f});
    right = normalize3(right, {1.f, 0.f, 0.f});

    if (r.distance < 1e-4f)
    {
        r.pan = 0.f;
        r.leftGain = 0.70710678f;
        r.rightGain = 0.70710678f;
        return r;
    }

    const Vec3 dir = {toSrc.x / r.distance, toSrc.y / r.distance, toSrc.z / r.distance};
    r.pan = std::clamp(dot3(dir, right), -1.f, 1.f);
    const float angle = (r.pan + 1.f) * (kPi * 0.25f); // equal-power: -1 → 0, +1 → π/2
    r.leftGain = std::cos(angle);
    r.rightGain = std::sin(angle);
    return r;
}

VernacularSoundscape::~VernacularSoundscape()
{
    stop();
}

void VernacularSoundscape::setStatus(const char* text)
{
    std::lock_guard<std::mutex> lock(mMutex);
    mStatus = text ? text : "";
}

std::string VernacularSoundscape::status() const
{
    std::lock_guard<std::mutex> lock(mMutex);
    return mStatus;
}

std::string VernacularSoundscape::debugLine() const
{
    Snapshot snap = capture();
    const Source& bowl = snap.sources[kBowlSlot];
    if (!bowl.enabled)
        return "spatial: bowl off";
    SpatialResult s = evaluate(snap.listener, bowl, snap.doppler);
    std::ostringstream oss;
    oss.setf(std::ios::fixed);
    oss.precision(1);
    oss << "bowl " << s.distance << "m  gain ";
    oss.precision(2);
    oss << (s.distanceGain * bowl.lookBoost * snap.masterGain) << "  dop ";
    oss.precision(3);
    oss << s.dopplerRatio << "  pan ";
    oss.setf(std::ios::showpos);
    oss.precision(2);
    oss << s.pan << "  ";
    oss.unsetf(std::ios::showpos);
    oss << (snap.mute ? "MUTE" : (snap.doppler ? "doppler on" : "doppler off"));
    return oss.str();
}

void VernacularSoundscape::publish(const Snapshot& snap)
{
    std::lock_guard<std::mutex> lock(mMutex);
    mSnap = snap;
}

VernacularSoundscape::Snapshot VernacularSoundscape::capture() const
{
    std::lock_guard<std::mutex> lock(mMutex);
    return mSnap;
}

void VernacularSoundscape::setMuted(bool mute)
{
    std::lock_guard<std::mutex> lock(mMutex);
    mSnap.mute = mute;
}

void VernacularSoundscape::setMasterGain(float gain)
{
    std::lock_guard<std::mutex> lock(mMutex);
    mSnap.masterGain = std::clamp(gain, 0.f, 2.f);
}

void VernacularSoundscape::setDopplerEnabled(bool enabled)
{
    std::lock_guard<std::mutex> lock(mMutex);
    mSnap.doppler = enabled;
}

void VernacularSoundscape::setListener(const Listener& listener)
{
    std::lock_guard<std::mutex> lock(mMutex);
    mSnap.listener = listener;
}

void VernacularSoundscape::setSource(int slot, const Source& source)
{
    if (slot < 0 || slot >= kMaxSources)
        return;
    std::lock_guard<std::mutex> lock(mMutex);
    mSnap.sources[static_cast<size_t>(slot)] = source;
}

void VernacularSoundscape::clearSources()
{
    std::lock_guard<std::mutex> lock(mMutex);
    mSnap.sources = {};
}

bool VernacularSoundscape::start()
{
    if (mRun.load())
        return mDeviceOk.load();

#if !defined(_WIN32)
    mDeviceOk = false;
    setStatus("audio: Windows-only stub");
    return false;
#else
    mRun = true;
    mDeviceOk = false;
    try
    {
        mThread = std::thread(&VernacularSoundscape::audioThreadMain, this);
    }
    catch (...)
    {
        mRun = false;
        setStatus("audio: thread spawn failed");
        return false;
    }
    setStatus("audio: starting WASAPI...");
    return true;
#endif
}

void VernacularSoundscape::stop()
{
    mRun = false;
    if (mThread.joinable())
        mThread.join();
    mDeviceOk = false;
    setStatus("audio: stopped");
}

void VernacularSoundscape::audioThreadMain()
{
#if !defined(_WIN32)
    setStatus("audio: Windows-only stub");
    mDeviceOk = false;
#else
    const HRESULT comHr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    const bool comOk = SUCCEEDED(comHr) || comHr == RPC_E_CHANGED_MODE;
    if (!comOk)
    {
        setStatus("audio: COM init failed");
        mDeviceOk = false;
        return;
    }

    auto uninitCom = [comHr]() {
        if (comHr != RPC_E_CHANGED_MODE)
            CoUninitialize();
    };
    HRESULT hr = S_OK;

    IMMDeviceEnumerator* pEnum = nullptr;
    hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), nullptr, CLSCTX_ALL, __uuidof(IMMDeviceEnumerator), (void**)&pEnum);
    if (FAILED(hr) || !pEnum)
    {
        setStatus("audio: no enumerator");
        mDeviceOk = false;
        uninitCom();
        return;
    }

    IMMDevice* pDevice = nullptr;
    hr = pEnum->GetDefaultAudioEndpoint(eRender, eConsole, &pDevice);
    pEnum->Release();
    if (FAILED(hr) || !pDevice)
    {
        setStatus("audio: no endpoint");
        mDeviceOk = false;
        uninitCom();
        return;
    }

    IAudioClient* pClient = nullptr;
    hr = pDevice->Activate(__uuidof(IAudioClient), CLSCTX_ALL, nullptr, (void**)&pClient);
    pDevice->Release();
    if (FAILED(hr) || !pClient)
    {
        setStatus("audio: activate failed");
        mDeviceOk = false;
        uninitCom();
        return;
    }

    WAVEFORMATEX* pWfx = nullptr;
    hr = pClient->GetMixFormat(&pWfx);
    if (FAILED(hr) || !pWfx)
    {
        setStatus("audio: mix format failed");
        pClient->Release();
        mDeviceOk = false;
        uninitCom();
        return;
    }

    const REFERENCE_TIME bufferDuration = 10000000; // 1s
    hr = pClient->Initialize(AUDCLNT_SHAREMODE_SHARED, 0, bufferDuration, 0, pWfx, nullptr);
    if (FAILED(hr))
    {
        setStatus("audio: init failed");
        CoTaskMemFree(pWfx);
        pClient->Release();
        mDeviceOk = false;
        uninitCom();
        return;
    }

    UINT32 bufferFrames = 0;
    pClient->GetBufferSize(&bufferFrames);
    IAudioRenderClient* pRender = nullptr;
    hr = pClient->GetService(__uuidof(IAudioRenderClient), (void**)&pRender);
    if (FAILED(hr) || !pRender)
    {
        setStatus("audio: render client failed");
        CoTaskMemFree(pWfx);
        pClient->Release();
        mDeviceOk = false;
        uninitCom();
        return;
    }

    const double sampleRate = pWfx->nSamplesPerSec > 0 ? double(pWfx->nSamplesPerSec) : 48000.0;
    const int channels = std::max(1, int(pWfx->nChannels));
    const bool isFloat = mixIsFloat32(pWfx);
    const bool isPcm16 = mixIsPcm16(pWfx);

    hr = pClient->Start();
    if (FAILED(hr))
    {
        setStatus("audio: start failed");
        pRender->Release();
        CoTaskMemFree(pWfx);
        pClient->Release();
        mDeviceOk = false;
        uninitCom();
        return;
    }

    mDeviceOk = true;
    setStatus(isFloat ? "audio: spatial WASAPI (float)" : (isPcm16 ? "audio: spatial WASAPI (pcm16)" : "audio: mix format silent"));

    double phase[kMaxSources][kMaxPartials] = {};
    uint32_t rng = 0xA341316Cu;
    float noiseLpf = 0.f;

    auto nextWhite = [&rng]() {
        rng ^= rng << 13;
        rng ^= rng >> 17;
        rng ^= rng << 5;
        return float(int32_t(rng)) * (1.f / 2147483648.f);
    };

    while (mRun.load())
    {
        UINT32 padding = 0;
        pClient->GetCurrentPadding(&padding);
        UINT32 available = bufferFrames - padding;
        if (available < 128)
        {
            Sleep(4);
            continue;
        }

        BYTE* pData = nullptr;
        if (FAILED(pRender->GetBuffer(available, &pData)) || !pData)
        {
            Sleep(4);
            continue;
        }

        Snapshot snap = capture();
        const bool canWrite = isFloat || isPcm16;

        if (!canWrite)
        {
            std::memset(pData, 0, size_t(available) * pWfx->nBlockAlign);
            pRender->ReleaseBuffer(available, AUDCLNT_BUFFERFLAGS_SILENT);
            Sleep(6);
            continue;
        }

        SpatialResult cached[kMaxSources];
        bool live[kMaxSources] = {};
        for (int s = 0; s < kMaxSources; ++s)
        {
            live[s] = snap.sources[static_cast<size_t>(s)].enabled && !snap.mute;
            if (live[s])
                cached[s] = evaluate(snap.listener, snap.sources[static_cast<size_t>(s)], snap.doppler);
        }

        float* fOut = isFloat ? reinterpret_cast<float*>(pData) : nullptr;
        int16_t* iOut = (!isFloat && isPcm16) ? reinterpret_cast<int16_t*>(pData) : nullptr;

        for (UINT32 i = 0; i < available; ++i)
        {
            float left = 0.f;
            float right = 0.f;
            if (!snap.mute)
            {
                for (int s = 0; s < kMaxSources; ++s)
                {
                    if (!live[s])
                        continue;
                    const Source& src = snap.sources[static_cast<size_t>(s)];
                    const SpatialResult& sp = cached[s];
                    const float gain = sp.distanceGain * src.lookBoost * snap.masterGain;
                    if (gain <= 1e-6f)
                        continue;

                    float mono = 0.f;
                    if (src.kind == SourceKind::Atmosphere)
                    {
                        noiseLpf = noiseLpf * 0.96f + nextWhite() * 0.04f;
                        mono = noiseLpf * src.amps[0];
                    }
                    else if (src.kind == SourceKind::Bowl || src.kind == SourceKind::ChirpHook)
                    {
                        const double dop = double(sp.dopplerRatio);
                        for (int p = 0; p < kMaxPartials; ++p)
                        {
                            if (src.amps[p] <= 1e-6f)
                                continue;
                            phase[s][p] += kTwoPi * double(src.freqs[p]) * dop / sampleRate;
                            if (phase[s][p] > kTwoPi)
                                phase[s][p] -= kTwoPi * std::floor(phase[s][p] / kTwoPi);
                            mono += src.amps[p] * float(std::sin(phase[s][p]));
                        }
                    }

                    left += mono * sp.leftGain * gain;
                    right += mono * sp.rightGain * gain;
                }
            }

            left = std::clamp(left, -1.f, 1.f);
            right = std::clamp(right, -1.f, 1.f);

            if (fOut)
            {
                if (channels == 1)
                {
                    fOut[i] = 0.5f * (left + right);
                }
                else
                {
                    fOut[i * channels + 0] = left;
                    fOut[i * channels + 1] = right;
                    for (int c = 2; c < channels; ++c)
                        fOut[i * channels + c] = 0.f;
                }
            }
            else if (iOut)
            {
                auto toI16 = [](float x) -> int16_t {
                    const float s = std::clamp(x, -1.f, 1.f) * 32767.f;
                    return int16_t(s);
                };
                if (channels == 1)
                {
                    iOut[i] = toI16(0.5f * (left + right));
                }
                else
                {
                    iOut[i * channels + 0] = toI16(left);
                    iOut[i * channels + 1] = toI16(right);
                    for (int c = 2; c < channels; ++c)
                        iOut[i * channels + c] = 0;
                }
            }
        }

        pRender->ReleaseBuffer(available, snap.mute ? AUDCLNT_BUFFERFLAGS_SILENT : 0);
        Sleep(6);
    }

    pClient->Stop();
    pRender->Release();
    CoTaskMemFree(pWfx);
    pClient->Release();
    uninitCom();
    mDeviceOk = false;
    setStatus("audio: stopped");
#endif
}

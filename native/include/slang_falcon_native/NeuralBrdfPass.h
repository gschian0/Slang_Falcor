#pragma once

#include "slang_falcon_native/WeightLoader.h"

#include <string>

namespace slang_falcon {

enum class ShadingMode { Teacher = 0, Neural = 1, Diff = 2 };

/// Render-pass façade. When linked with Falcor, binds weight buffers and draws
/// a fullscreen neural BRDF. Standalone build validates weights + prints plan.
class NeuralBrdfPass {
public:
    bool loadWeightsFile(const std::string& path);
    void setMode(ShadingMode mode) { mode_ = mode; }
    ShadingMode mode() const { return mode_; }
    void toggleTeacherNeural();

    /// true when VK_NV_cooperative_vector path is selected at runtime.
    bool coopVecAvailable() const { return coopVec_; }
    void setCoopVecAvailable(bool v) { coopVec_ = v; }

    const MlpWeights& weights() const { return weights_; }
    bool ready() const { return ready_; }

    /// Execute one frame (Falcor hooks in later). Standalone: no-op success.
    bool execute();

private:
    MlpWeights weights_{};
    ShadingMode mode_ = ShadingMode::Neural;
    bool coopVec_ = false;
    bool ready_ = false;
};

}  // namespace slang_falcon

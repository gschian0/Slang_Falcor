#include "slang_falcon_native/NeuralTrainPass.h"

#include <iostream>

namespace slang_falcon {

float NeuralTrainPass::step() {
    if (!enabled_ || !infer_.ready()) return -1.0f;
    ++iteration_;
    // Integration point with Falcor + Slang autodiff / CoopVec TrainingMLP:
    // sample BRDF features → teacher Disney → bwd through MLP → Adam update
    // into the same weight buffer used by NeuralBrdfPass.
    std::cout << "[NeuralTrainPass] step " << iteration_ << " lr=" << lr_
              << (infer_.coopVecAvailable() ? " (CoopVec)" : " (scalar)") << "\n";
    return 0.0f;
}

}  // namespace slang_falcon

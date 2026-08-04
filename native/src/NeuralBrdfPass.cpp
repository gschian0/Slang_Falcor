#include "slang_falcon_native/NeuralBrdfPass.h"

#include <iostream>

namespace slang_falcon {

bool NeuralBrdfPass::loadWeightsFile(const std::string& path) {
    weights_ = loadWeights(path);
    ready_ = !weights_.layers.empty();
    std::cout << "[NeuralBrdfPass] loaded " << weights_.layers.size()
              << " layers from " << path << "\n";
    return ready_;
}

void NeuralBrdfPass::toggleTeacherNeural() {
    if (mode_ == ShadingMode::Teacher)
        mode_ = ShadingMode::Neural;
    else
        mode_ = ShadingMode::Teacher;
    std::cout << "[NeuralBrdfPass] mode="
              << (mode_ == ShadingMode::Teacher ? "teacher" : "neural") << "\n";
}

bool NeuralBrdfPass::execute() {
    if (!ready_) return false;
    // Falcor integration point:
    //  - upload weights_.flatten() to ByteAddressBuffer
    //  - bind NeuralBrdf.slang fullscreen pass
    //  - if coopVec_: InferenceMLP CoopVec path else scalar MLP
    return true;
}

}  // namespace slang_falcon

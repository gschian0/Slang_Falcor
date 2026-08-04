#pragma once

#include "slang_falcon_native/NeuralBrdfPass.h"

namespace slang_falcon {

/// Optional in-process training pass (autodiff + CoopVec when available).
/// Phase 2 train todo: live fine-tune against Disney teacher in the viewport.
class NeuralTrainPass {
public:
    explicit NeuralTrainPass(NeuralBrdfPass& infer) : infer_(infer) {}

    void setEnabled(bool e) { enabled_ = e; }
    bool enabled() const { return enabled_; }
    void setLearningRate(float lr) { lr_ = lr; }

    /// One training step over a random batch. Returns mean loss (or -1 if inactive).
    float step();

private:
    NeuralBrdfPass& infer_;
    bool enabled_ = false;
    float lr_ = 1e-3f;
    int iteration_ = 0;
};

}  // namespace slang_falcon

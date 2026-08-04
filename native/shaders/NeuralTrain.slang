// SPDX-License-Identifier: Apache-2.0
// Optional in-process training kernels (CoopVec TrainingMLP hook).

module NeuralTrain;

/// Entry points for live fine-tune against Disney teacher.
/// Wired from NeuralTrainPass::step() when --train is enabled.

struct TrainConstants
{
    float learningRate;
    int iteration;
    uint seed;
    uint batchSize;
};

/// Placeholder: host dispatches a compute grid of train_sample like Phase 1.
void trainDummy(TrainConstants cb)
{
    // See slang/train_brdf.slang for the reference algorithm.
}

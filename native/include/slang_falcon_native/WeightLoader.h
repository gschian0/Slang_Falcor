#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace slang_falcon {

struct LayerDesc {
    uint32_t inputs = 0;
    uint32_t outputs = 0;
    std::vector<float> biases;   // outputs
    std::vector<float> weights;  // outputs * inputs, row-major
};

struct MlpWeights {
    uint32_t version = 0;
    std::vector<LayerDesc> layers;

    /// Flatten biases+weights per layer (upload order for ByteAddressBuffer).
    std::vector<float> flatten() const;
};

/// Load Phase 1 SFMLP001 binary. Throws std::runtime_error on failure.
MlpWeights loadWeights(const std::string& path);

}  // namespace slang_falcon

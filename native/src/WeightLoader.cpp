#include "slang_falcon_native/WeightLoader.h"

#include <cstring>
#include <fstream>
#include <stdexcept>

namespace slang_falcon {
namespace {

constexpr char kMagic[8] = {'S', 'F', 'M', 'L', 'P', '0', '0', '1'};

template <typename T>
T readPod(std::ifstream& in) {
    T v{};
    in.read(reinterpret_cast<char*>(&v), sizeof(T));
    if (!in) throw std::runtime_error("Unexpected EOF in weight file");
    return v;
}

}  // namespace

std::vector<float> MlpWeights::flatten() const {
    std::vector<float> out;
    for (const auto& layer : layers) {
        out.insert(out.end(), layer.biases.begin(), layer.biases.end());
        out.insert(out.end(), layer.weights.begin(), layer.weights.end());
    }
    return out;
}

MlpWeights loadWeights(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("Failed to open weights: " + path);

    char magic[8]{};
    in.read(magic, 8);
    if (std::memcmp(magic, kMagic, 8) != 0)
        throw std::runtime_error("Bad weight magic (expected SFMLP001)");

    MlpWeights mlp;
    mlp.version = readPod<uint32_t>(in);
    if (mlp.version != 1) throw std::runtime_error("Unsupported weight version");

    const uint32_t nLayers = readPod<uint32_t>(in);
    mlp.layers.resize(nLayers);
    for (auto& layer : mlp.layers) {
        layer.inputs = readPod<uint32_t>(in);
        layer.outputs = readPod<uint32_t>(in);
    }
    for (auto& layer : mlp.layers) {
        layer.biases.resize(layer.outputs);
        layer.weights.resize(static_cast<size_t>(layer.outputs) * layer.inputs);
        in.read(reinterpret_cast<char*>(layer.biases.data()),
                static_cast<std::streamsize>(layer.biases.size() * sizeof(float)));
        in.read(reinterpret_cast<char*>(layer.weights.data()),
                static_cast<std::streamsize>(layer.weights.size() * sizeof(float)));
        if (!in) throw std::runtime_error("Truncated weight payload");
    }
    return mlp;
}

}  // namespace slang_falcon

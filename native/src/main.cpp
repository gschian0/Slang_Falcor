#include "slang_falcon_native/FalcorPhase0Stub.h"
#include "slang_falcon_native/HotReload.h"
#include "slang_falcon_native/NeuralBrdfPass.h"
#include "slang_falcon_native/NeuralTrainPass.h"

#include <filesystem>
#include <iostream>
#include <string>

namespace fs = std::filesystem;

static void printUsage(const char* argv0) {
    std::cout
        << "VERNACULAR native — Falcor/Vulkan neural BRDF host (scaffold)\n"
        << "Usage: " << argv0 << " --weights <SFMLP001.bin> [--train] [--coopvec] [--phase0]\n"
        << "Keys (when Falcor viewport is wired): T toggle teacher/neural, F5 reload, R train step\n";
}

int main(int argc, char** argv) {
    std::string weightsPath;
    bool enableTrain = false;
    bool wantCoopVec = false;
    bool showPhase0 = false;

    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--weights" && i + 1 < argc) weightsPath = argv[++i];
        else if (a == "--train") enableTrain = true;
        else if (a == "--coopvec") wantCoopVec = true;
        else if (a == "--phase0") showPhase0 = true;
        else if (a == "--help" || a == "-h") {
            printUsage(argv[0]);
            slang_falcon::printFalcorPhase0Checklist();
            return 0;
        }
    }

    if (showPhase0) {
        slang_falcon::printFalcorPhase0Checklist();
        return 0;
    }

    if (weightsPath.empty()) {
        // Default relative to repo when launched from native/build
        const char* candidates[] = {
            "../assets/weights/brdf_mlp.bin",
            "../../assets/weights/brdf_mlp.bin",
            "assets/weights/brdf_mlp.bin",
        };
        for (const char* c : candidates) {
            if (fs::exists(c)) {
                weightsPath = c;
                break;
            }
        }
    }

    if (weightsPath.empty() || !fs::exists(weightsPath)) {
        printUsage(argv[0]);
        std::cerr << "error: weights file not found. Train Phase 1 first.\n";
        slang_falcon::printFalcorPhase0Checklist();
        return 1;
    }

    slang_falcon::NeuralBrdfPass pass;
    pass.setCoopVecAvailable(wantCoopVec);
    if (!pass.loadWeightsFile(weightsPath)) return 2;

    slang_falcon::HotReload reload;
    const fs::path shader = fs::path(SF_SHADER_DIR) / "NeuralBrdf.slang";
    reload.watch(shader, [&](const fs::path& p) {
        std::cout << "Would recompile Falcor program from " << p << "\n";
    });

    slang_falcon::NeuralTrainPass train(pass);
    train.setEnabled(enableTrain);

    // Demo: toggle + optional train step + hot-reload poll once
    pass.toggleTeacherNeural();
    pass.toggleTeacherNeural();
    if (enableTrain) train.step();
    reload.poll();
    pass.execute();

    std::cout << "VERNACULAR native scaffold OK. Wire Falcor viewport next (see native/README.md).\n"
              << "layers=" << pass.weights().layers.size()
              << " coopVecFlag=" << (pass.coopVecAvailable() ? 1 : 0) << "\n";
    slang_falcon::printFalcorPhase0Checklist();
    return 0;
}

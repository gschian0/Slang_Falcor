#include "slang_falcon_native/FalcorPhase0Stub.h"

#include <iostream>

namespace slang_falcon {

void printFalcorPhase0Checklist() {
    std::cout
        << "\n=== VERNACULAR native — Falcor Phase 0 checklist ===\n"
        << "1. powershell -File native/scripts/fetch_falcor.ps1\n"
        << "2. Build Falcor once from native/external/Falcor (see Falcor README / packman)\n"
        << "3. cmake -B build-falcor -DSF_FALCOR_ROOT=.../external/Falcor\n"
        << "4. Implement SampleApp in FalcorPhase0App.cpp: camera + one mesh + Slang pass\n"
        << "5. Keep HotReload on native/shaders/NeuralBrdf.slang (F5)\n"
        << "Do not block on SAM — that is plan Phase 2.\n"
        << "Plan: docs/plans/falcor-viewport-sam.md\n";
}

}  // namespace slang_falcon

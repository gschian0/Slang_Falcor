cmake_minimum_required(VERSION 3.24)
project(SlangFalconNative LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(SF_FETCH_FALCOR "Prefer FetchContent / external Falcor tree (large)" OFF)
option(SF_BUILD_STANDALONE "Build standalone scaffold without linking Falcor" ON)
set(SF_FALCOR_ROOT "" CACHE PATH "Path to a local Falcor checkout (e.g. native/external/Falcor)")

add_library(slang_falcon_native_core STATIC
    src/WeightLoader.cpp
    src/HotReload.cpp
    src/NeuralBrdfPass.cpp
    src/NeuralTrainPass.cpp
)
target_include_directories(slang_falcon_native_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_compile_definitions(slang_falcon_native_core PUBLIC
    SF_SHADER_DIR="${CMAKE_CURRENT_SOURCE_DIR}/shaders"
)

if(SF_BUILD_STANDALONE)
    add_executable(SlangFalconNative
        src/main.cpp
        src/FalcorPhase0Stub.cpp
    )
    target_link_libraries(SlangFalconNative PRIVATE slang_falcon_native_core)
endif()

# --- Phase 0 Falcor discovery (do not vendor; do not block standalone smoke) ---
if(NOT SF_FALCOR_ROOT AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/external/Falcor/CMakeLists.txt")
    set(SF_FALCOR_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/external/Falcor" CACHE PATH "Path to Falcor" FORCE)
endif()

if(SF_FETCH_FALCOR AND NOT SF_FALCOR_ROOT)
    include(FetchContent)
    message(STATUS "SF_FETCH_FALCOR=ON — prefer scripts/fetch_falcor.ps1 then -DSF_FALCOR_ROOT=...")
    message(STATUS "  FetchContent auto-clone is disabled by default (Falcor + packman is multi-GB).")
    message(STATUS "  Run: powershell -File native/scripts/fetch_falcor.ps1")
endif()

if(SF_FALCOR_ROOT AND EXISTS "${SF_FALCOR_ROOT}/CMakeLists.txt")
    message(STATUS "Falcor tree found: ${SF_FALCOR_ROOT}")
    message(STATUS "Phase 0 next: build Falcor itself once, then wire SlangFalconFalcor SampleApp")
    message(STATUS "  (see native/README.md § Phase 0). add_subdirectory(Falcor) is intentionally not")
    message(STATUS "  enabled yet — Falcor's CMake/packman must succeed on this machine first.")
    # Future:
    #   add_subdirectory(${SF_FALCOR_ROOT} ${CMAKE_BINARY_DIR}/falcor EXCLUDE_FROM_ALL)
    #   add_executable(SlangFalconFalcor src/FalcorPhase0App.cpp ...)
    #   target_link_libraries(SlangFalconFalcor PRIVATE Falcor ...)
else()
    message(STATUS "Falcor not present — standalone scaffold only. Fetch with:")
    message(STATUS "  powershell -File ${CMAKE_CURRENT_SOURCE_DIR}/scripts/fetch_falcor.ps1")
endif()

install(DIRECTORY shaders/ DESTINATION shaders)
install(FILES README.md DESTINATION .)

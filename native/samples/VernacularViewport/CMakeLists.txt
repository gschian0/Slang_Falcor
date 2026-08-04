add_falcor_executable(VernacularViewport)

target_sources(VernacularViewport PRIVATE
    VernacularViewport.cpp
    VernacularViewport.h
    VernacularViewport.3d.slang
)

target_copy_shaders(VernacularViewport Samples/VernacularViewport)

target_source_group(VernacularViewport "Samples")

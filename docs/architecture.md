# Architecture overview

```
labs / CLI  --train-->  SFMLP001 weights  -->  Falcor CoopVec infer
                                   \\
                                    +-->  WebGPU float MLP demos
```

Shared Slang sources live in `slang/` for Phase 1 and are mirrored/adapted under
`native/shaders/` for the Falcor host. Web demos reimplement the float forward
pass in JS/WGSL against the same binary layout (`docs/weight_format.md`).

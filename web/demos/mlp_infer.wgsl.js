// Optional WGSL compute sketch for float MLP inference (no CoopVec).
// Host uploads SFMLP001 layers as storage buffers; this is a reference kernel.

export const MLP_INFER_WGSL = /* wgsl */ `
struct LayerMeta { inputs: u32, outputs: u32, weightOffset: u32, biasOffset: u32, };

@group(0) @binding(0) var<storage, read> features: array<f32>;
@group(0) @binding(1) var<storage, read> weights: array<f32>;
@group(0) @binding(2) var<storage, read> biases: array<f32>;
@group(0) @binding(3) var<storage, read_write> output: array<f32>;

fn relu(x: f32) -> f32 { return max(x, 0.0); }
fn softplus(x: f32) -> f32 { return log(1.0 + exp(x)); }

// Single-layer helper; multi-layer dispatch is orchestrated on the CPU/JS side
// for the teaching demo (see brdf_compare.js mlpForward).
@compute @workgroup_size(1)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  // Placeholder entry — full multi-layer binding matches docs/weight_format.md.
  _ = gid;
}
`;

/** Parse SFMLP001 weight files (see docs/weight_format.md). */

export function parseSfmlp(buffer) {
  const view = new DataView(buffer);
  const magic = String.fromCharCode(...new Uint8Array(buffer, 0, 8));
  if (magic !== "SFMLP001") throw new Error(`Bad magic: ${magic}`);
  const version = view.getUint32(8, true);
  const nLayers = view.getUint32(12, true);
  if (version !== 1) throw new Error(`Unsupported version ${version}`);
  let offset = 16;
  const shapes = [];
  for (let i = 0; i < nLayers; i++) {
    const inputs = view.getUint32(offset, true);
    const outputs = view.getUint32(offset + 4, true);
    shapes.push({ inputs, outputs });
    offset += 8;
  }
  const layers = [];
  for (const shape of shapes) {
    const biases = new Float32Array(shape.outputs);
    for (let i = 0; i < shape.outputs; i++, offset += 4) {
      biases[i] = view.getFloat32(offset, true);
    }
    const weights = new Float32Array(shape.outputs * shape.inputs);
    for (let i = 0; i < weights.length; i++, offset += 4) {
      weights[i] = view.getFloat32(offset, true);
    }
    layers.push({ ...shape, biases, weights });
  }
  return { version, layers };
}

export function relu(x) {
  return x > 0 ? x : 0;
}

export function softplus(x) {
  if (x > 20) return x;
  return Math.log1p(Math.exp(x));
}

/** CPU MLP forward matching Phase 1. */
export function mlpForward(features, mlp) {
  let x = Float32Array.from(features);
  for (let li = 0; li < mlp.layers.length; li++) {
    const layer = mlp.layers[li];
    const y = new Float32Array(layer.outputs);
    for (let row = 0; row < layer.outputs; row++) {
      let sum = layer.biases[row];
      const base = row * layer.inputs;
      for (let col = 0; col < layer.inputs; col++) {
        sum += layer.weights[base + col] * x[col];
      }
      y[row] = li < mlp.layers.length - 1 ? relu(sum) : softplus(sum);
    }
    x = y;
  }
  return x;
}

function schlick(u) {
  const m = Math.min(Math.max(1 - u, 0), 1);
  const m2 = m * m;
  return m2 * m2 * m;
}

export function disneyCpu(albedo, L, V, N, roughness) {
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const NdotL = dot(N, L);
  const NdotV = dot(N, V);
  if (NdotL < 0 || NdotV < 0) return [0, 0, 0];
  const H = [L[0] + V[0], L[1] + V[1], L[2] + V[2]];
  const hn = Math.hypot(H[0], H[1], H[2]) || 1;
  H[0] /= hn; H[1] /= hn; H[2] /= hn;
  const NdotH = dot(N, H);
  const LdotH = dot(L, H);
  const metallic = 0;
  const specular = 0.5;
  const Cspec0 = albedo.map((c) => (1 - metallic) * specular * 0.08 + metallic * c);
  const FL = schlick(NdotL);
  const FV = schlick(NdotV);
  const Fd90 = 0.5 + 2 * LdotH * LdotH * roughness;
  const Fd = (1 + (Fd90 - 1) * FL) * (1 + (Fd90 - 1) * FV);
  const a = Math.max(roughness * roughness, 1e-4);
  const a2 = a * a;
  const t = 1 + (a2 - 1) * NdotH * NdotH;
  const Ds = a2 / (Math.PI * t * t);
  const FH = schlick(LdotH);
  const Fs = Cspec0.map((c) => c + (1 - c) * FH);
  const smith = (nd) => {
    const aa = a * a;
    const bb = nd * nd;
    return 1 / (nd + Math.sqrt(aa + bb - aa * bb));
  };
  const Gs = smith(NdotL) * smith(NdotV);
  const out = [0, 0, 0];
  for (let i = 0; i < 3; i++) {
    const diff = (1 / Math.PI) * Fd * albedo[i] * (1 - metallic);
    out[i] = (diff + Gs * Fs[i] * Ds) * Math.max(NdotL, 0);
  }
  return out;
}

export function packFeatures(L, V, N, roughness) {
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const H = [L[0] + V[0], L[1] + V[1], L[2] + V[2]];
  const hn = Math.hypot(H[0], H[1], H[2]) || 1;
  H[0] /= hn; H[1] /= hn; H[2] /= hn;
  const sat = (x) => Math.min(Math.max(x, 0), 1);
  return [sat(dot(N, L)), sat(dot(N, V)), sat(dot(N, H)), sat(dot(L, H)), sat(roughness)];
}

export async function loadWeights(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status}`);
  return parseSfmlp(await res.arrayBuffer());
}

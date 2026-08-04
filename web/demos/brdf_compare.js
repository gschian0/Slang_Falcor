import {
  disneyCpu,
  loadWeights,
  mlpForward,
  packFeatures,
  parseSfmlp,
} from "./mlp.js";

const statusEl = document.getElementById("status");
const canvas = document.getElementById("cv");
const ctx = canvas.getContext("2d");

function tonemap(rgb) {
  return rgb.map((c) => Math.min(255, Math.max(0, Math.floor((c / (c + 1)) * 255))));
}

function renderStrip(mlp, w = 256, h = 256) {
  const albedo = [0.8, 0.15, 0.1];
  const N = [0, 0, 1];
  let V = [0.2, 0.3, 0.9];
  const vn = Math.hypot(...V);
  V = V.map((c) => c / vn);

  const img = ctx.createImageData(w * 3, h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const ndotl = (x + 0.5) / w;
      const rough = 0.05 + 0.9 * ((y + 0.5) / h);
      const L = [Math.sqrt(Math.max(0, 1 - ndotl * ndotl)), 0, ndotl];
      const feat = packFeatures(L, V, N, rough);
      const teacher = disneyCpu(albedo, L, V, N, rough);
      const pred = Array.from(mlpForward(feat, mlp));
      const diff = teacher.map((t, i) => Math.abs(t - pred[i]) * 4);
      const panels = [teacher, pred, diff].map(tonemap);
      for (let p = 0; p < 3; p++) {
        const i = ((y * w * 3) + p * w + x) * 4;
        img.data[i] = panels[p][0];
        img.data[i + 1] = panels[p][1];
        img.data[i + 2] = panels[p][2];
        img.data[i + 3] = 255;
      }
    }
  }
  canvas.width = w * 3;
  canvas.height = h;
  ctx.putImageData(img, 0, 0);
}

async function tryWebGpuNote() {
  if (!navigator.gpu) {
    statusEl.textContent = "WebGPU unavailable — using CPU float MLP (still valid for teaching).";
    return;
  }
  try {
    const adapter = await navigator.gpu.requestAdapter();
    if (adapter) statusEl.textContent += " WebGPU adapter present (CPU path used for SFMLP parity).";
  } catch {
    /* ignore */
  }
}

async function fromUrl(url) {
  statusEl.textContent = `Loading ${url}…`;
  const mlp = await loadWeights(url);
  renderStrip(mlp);
  statusEl.textContent = `Loaded ${mlp.layers.length} layers from ${url}.`;
  await tryWebGpuNote();
}

document.getElementById("btn-default").addEventListener("click", () => {
  // Prefer repo-root serve: /assets/weights/brdf_mlp.bin
  const candidates = [
    "../../assets/weights/brdf_mlp.bin",
    "/assets/weights/brdf_mlp.bin",
  ];
  (async () => {
    let lastErr;
    for (const url of candidates) {
      try {
        await fromUrl(url);
        return;
      } catch (e) {
        lastErr = e;
      }
    }
    statusEl.textContent = `Could not load weights (${lastErr}). Train Phase 1 or choose a .bin file.`;
  })();
});

document.getElementById("file").addEventListener("change", async (ev) => {
  const file = ev.target.files?.[0];
  if (!file) return;
  const mlp = parseSfmlp(await file.arrayBuffer());
  renderStrip(mlp);
  statusEl.textContent = `Loaded ${file.name} (${mlp.layers.length} layers).`;
});

// Auto-try default on load
document.getElementById("btn-default").click();

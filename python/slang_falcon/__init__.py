"""VERNACULAR (package slang_falcon) — Phase 1: SlangPy neural shading train / infer."""

from __future__ import annotations

from pathlib import Path

__version__ = "0.1.0"

REPO_ROOT = Path(__file__).resolve().parents[2]
SLANG_DIR = REPO_ROOT / "slang"
ASSETS_DIR = REPO_ROOT / "assets"
WEIGHTS_DIR = ASSETS_DIR / "weights"
OUTPUT_DIR = ASSETS_DIR / "output"

# Default BRDF MLP architecture (must match slang/mlp.slang BrdfMLP)
BRDF_LAYER_SIZES = ((5, 32), (32, 32), (32, 3))

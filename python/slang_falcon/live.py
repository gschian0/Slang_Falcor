"""VERNACULAR live shader preview: edit .slang in-window, hotswap via temp, see update.

Product name: **VERNACULAR**. Package module remains ``slang_falcon.live``.

Usage:
    python -m slang_falcon.live
    python -m slang_falcon.vernacular
    vernacular --lesson 0   # console script after pip install -e .
    python -m slang_falcon.live --lesson 0
    python -m slang_falcon.live --lesson bos/00_hello
    python -m slang_falcon.live --shader slang/lab_kernels.slang --entry hello_pixel --size 640
    python -m slang_falcon.live --school-3d --files temple_vs.slang temple_ps.slang temple_diff.slang
    python -m slang_falcon.live --once   # smoke: one frame, no window

Curriculum nav: ``[`` / Left / PageUp = prev, ``]`` / Right / PageDown = next,
``Ctrl+[`` / ``Ctrl+]`` works even while editing, ``L`` = list lessons,
``0``–``9`` = jump by index, ``<`` ``>`` buttons on the code toolbar.
Lesson strip under the preview shows title, blurb, and Try tips from the lesson markdown.

Editor: Ctrl+Z undo, Ctrl+Y / Ctrl+Shift+Z redo, Ctrl+C/X/V clipboard,
click-drag / Shift+arrows select. Window is resizable (shader letterboxes).

Entries that declare ``float time`` receive seconds since live start (or ``--time`` with ``--once``).
Entries that declare ``float2 mouse`` / ``float2 mouse_delta`` / ``int mouse_down`` get
ShaderToy-style mouse uniforms. Lessons with ``interactive_mouse`` use primary-drag on the
shader for look-around; move the window via the title bar, Alt+drag, or middle-button drag.

Color-like ``float3`` / ``float4`` entry params (name hints: color, colour, albedo, tint,
base, sky, fog, light, rgb, col, …) get a Color panel: swatches, HSV square + hue bar,
RGB sliders — live-updates the running shader. Panel hides when none apply. Hover
``float3`` / ``float4`` or a color-like param name in the editor to focus that swatch.

Lessons with a curriculum ``texture`` path (or an entry that declares ``Texture2D``)
bind a SlangPy Texture2D + SamplerState. Missing GPU texture falls back to numpy UV
sampling when the entry is texture-driven.

Fullscreen: **F11** / green = window FS (prefer this). **F10** / **Shift+F11** / cyan =
shader-only FS — known issue: can black out the display; fix later (borderless windowed,
never exclusive). **Esc** exits either mode (then quits when windowed).
"""

from __future__ import annotations

import argparse
import gc
import math
import re
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

try:
    from numba import njit, prange

    _HAS_NUMBA = True
except ImportError:  # pragma: no cover - optional accel
    _HAS_NUMBA = False

    def njit(*_a: Any, **_k: Any):  # type: ignore[misc]
        def wrap(fn: Any) -> Any:
            return fn

        return wrap

    def prange(*args: Any) -> Any:  # type: ignore[misc]
        return range(*args)

from slang_falcon import ASSETS_DIR, REPO_ROOT, SLANG_DIR
from slang_falcon.code_editor import CodeEditor
from slang_falcon.curriculum import (
    Lesson,
    find_lesson,
    format_lesson_list,
    lesson_banner_lines,
    load_curriculum,
)
from slang_falcon.device import clear_module_cache, get_device, load_module_from_path
from slang_falcon.win32_shaped import (
    COLORKEY_RGB,
    Win32ShapedHost,
    is_windows,
    wobble_pad_x,
)

# Editor → temp write + recompile after typing stops.
_EDIT_DEBOUNCE_S = 0.45

# Window chrome: shader square | code square | lesson strip | console spanning both.
_CONSOLE_H = 132
_LESSON_STRIP_H = 64  # on-screen example explanation (title / blurb / Try)
_COLOR_PANEL_H = 100  # swatches + HSV + RGB when entry has color uniforms
_CODE_PANEL_MIN_W = 360  # floor when the window is squeezed; default tracks shader size
_SHADER_VIEW_MIN = 180  # min letterbox area for the shader viewport
_PANEL_PAD = 10
_CODE_LINE_GAP = 3  # extra leading so glyphs/caret clear the next row
_CONSOLE_LINE_GAP = 2  # console row leading (avoids glyph clip at larger sizes)
_CHROME = 2  # outer embossed bevel thickness (px); thinner = less blocky corners
_DIVIDER = 3  # embossed divider between regions (px)
_TITLE_BAR_H = 36  # frosted Mac-style drag bar (Windows borderless / shaped host)
_CORNER_RADIUS = 10  # soft outer corners (matches Win32 rounded HRGN when settled)
_BTN_BAR_H = 32
_BTN_W = 60
_BTN_H = 24
_BTN_GAP = 6
_LESSON_BG = (22, 28, 38)
_LESSON_TITLE = (210, 216, 228)
_LESSON_BODY = (148, 160, 178)
_COLOR_BG = (20, 24, 32)
_COLOR_LABEL = (168, 176, 190)
_COLOR_MUTED = (110, 120, 136)
_COLOR_SLIDER_TRACK = (40, 46, 58)
_COLOR_SLIDER_FILL = (120, 132, 150)
# Token hints for float3/float4 entry params treated as pickable colors.
_COLOR_NAME_HINTS = frozenset(
    {
        "color",
        "colour",
        "albedo",
        "tint",
        "base",
        "sky",
        "fog",
        "light",
        "rgb",
        "col",
        "diffuse",
        "specular",
        "emissive",
        "hue",
        "paint",
        "ink",
        "glow",
        "shade",
        "bg",
        "background",
    }
)
_COLOR_NAME_EXCLUDE = frozenset(
    {
        "position",
        "pos",
        "normal",
        "dir",
        "direction",
        "offset",
        "scale",
        "size",
        "center",
        "centre",
        "origin",
        "velocity",
        "force",
        "extent",
        "bounds",
        "xyz",
        "uvw",
        "point",
        "coord",
    }
)
# Live UI type sizes (SysFont consolas; antialiased render=True)
_FONT_CONSOLE = 16
_FONT_CODE = 16
_FONT_BTN = 14
_FONT_TITLE = 18
_LABEL_AA_SCALE = 2  # title/labels: render at Nx then smoothscale down
_PRESENT_SHARPEN = 0.18  # light unsharp on present path (pairs with 3x3 AA)
_MAX_CONSOLE_LINES = 250
_CONSOLE_COLOR = (40, 220, 90)
_CONSOLE_BG = (8, 10, 12)
_CODE_BG = (18, 22, 30)
_SEL_BG = (52, 72, 110)  # selection highlight behind glyphs
_BTN_FACE = (88, 94, 108)
_BTN_LABEL = (196, 202, 214)  # soft metal on chrome buttons (not neon-white)
_CARET = (240, 240, 245)
# Futuristic glass / brushed-metal chrome
_TITLE_FACE = (30, 34, 42)  # base under frosted overlay
_TITLE_TEXT = (156, 164, 178)  # mid-tone steel face — readable on frost, not washed out
_TITLE_EMBOSS_LIGHT = (200, 208, 220)  # classic NW highlight
_TITLE_EMBOSS_DARK = (40, 46, 56)  # classic SE shadow
_TITLE_GLASS_TOP = (235, 242, 255, 68)
_TITLE_GLASS_MID = (105, 116, 136, 30)
_TITLE_GLASS_BOT = (18, 22, 30, 82)
_TRAFFIC_RED = (255, 95, 86)
_TRAFFIC_RED_RIM = (170, 48, 42)
_TRAFFIC_YELLOW = (255, 189, 46)
_TRAFFIC_YELLOW_RIM = (180, 128, 28)
_TRAFFIC_GREEN = (39, 201, 63)
_TRAFFIC_GREEN_RIM = (24, 138, 44)
_TRAFFIC_CYAN = (64, 180, 255)  # 4th bead — shader-only fullscreen
_TRAFFIC_CYAN_RIM = (28, 110, 170)
_TRAFFIC_R = 6
_TRAFFIC_GAP = 7  # tighter cluster
_TRAFFIC_PAD_X = 13
_TRAFFIC_COUNT = 4  # red close · yellow · green window-FS · cyan shader-FS
# Fullscreen modes for the live IDE (None = windowed).
_FS_WINDOW = "window"  # whole chrome fills the display
_FS_SHADER = "shader"  # shader fills the display; chrome hidden
# Soft steel / glass bevel — muted highlights, less chunky pixels
_BEVEL_LIGHT = (186, 196, 210)
_BEVEL_DARK = (30, 34, 42)
_BEVEL_FACE = (56, 62, 74)
_BEVEL_SPEC = (210, 218, 230)  # soft specular hairline on raised edges
_DEFAULT_LIVE_SIZE = 640  # wider default render / window than classic 512

# Slang / HLSL-ish highlighting
_SLANG_KEYWORDS = frozenset(
    {
        "as",
        "break",
        "case",
        "catch",
        "continue",
        "default",
        "discard",
        "do",
        "else",
        "enum",
        "export",
        "extension",
        "extern",
        "false",
        "for",
        "get",
        "if",
        "import",
        "in",
        "inout",
        "interface",
        "let",
        "module",
        "namespace",
        "no_diff",
        "out",
        "public",
        "private",
        "internal",
        "return",
        "set",
        "static",
        "struct",
        "switch",
        "this",
        "throw",
        "true",
        "try",
        "typedef",
        "typeof",
        "uniform",
        "var",
        "while",
        "with",
    }
)
_SLANG_TYPES = frozenset(
    {
        "void",
        "bool",
        "int",
        "uint",
        "float",
        "double",
        "half",
        "int2",
        "int3",
        "int4",
        "uint2",
        "uint3",
        "uint4",
        "float2",
        "float3",
        "float4",
        "double2",
        "double3",
        "double4",
        "bool2",
        "bool3",
        "bool4",
        "half2",
        "half3",
        "half4",
        "float2x2",
        "float3x3",
        "float4x4",
        "matrix",
        "vector",
        "string",
        "Texture2D",
        "Texture3D",
        "TextureCube",
        "SamplerState",
        "RWTexture2D",
        "StructuredBuffer",
        "RWStructuredBuffer",
        "ConstantBuffer",
        "ByteAddressBuffer",
        "RWByteAddressBuffer",
    }
)
_TOKEN_COLORS = {
    "keyword": (86, 156, 214),
    "type": (78, 201, 176),
    "comment": (106, 153, 85),
    "string": (206, 145, 120),
    "number": (181, 206, 168),
    "attr": (197, 134, 192),
    "ident": (220, 220, 220),
    "default": (210, 210, 215),
}

# Compiz jello wobble: dense 2D control mesh + Catmull-Rom field upsample.
# Sensitivity dialed down ~25–30% from the "too twitchy" Compiz defaults.
_WOBBLE_COLS = 48
_WOBBLE_ROWS = 32
_WOBBLE_REF_ROWS = 16  # continuum couple scaling reference (pre-density default)
_WOBBLE_SPRING = 16.0
_WOBBLE_DAMP = 5.2
_WOBBLE_COUPLE = 38.0
_WOBBLE_MAX_PX = 42.0
_WOBBLE_DRAG_GAIN = 5.0  # velocity impulse per px of OS window move
_WOBBLE_DRAG_DISP = 0.40  # immediate mesh displacement fraction of dx
_WOBBLE_POS_EPS = 1  # min window-pos delta (px) to count as a drag tick
# Settled thresholds: identity blit + snap mesh to zero (skip warp/region rebuild).
_WOBBLE_STILL_X = 0.2
_WOBBLE_STILL_V = 0.8
# Silhouette while deforming: every content row (settled uses round-rect).
_WOBBLE_OUTLINE_STEP = 1
# Full-res remap cost (profiled once when wobble first runs).
_WOBBLE_PROFILE_ONCE = True


@njit(cache=True, parallel=True)  # type: ignore[misc]
def _warp_horizontal_nearest_numba(
    img: np.ndarray,
    map_x: np.ndarray,
    out: np.ndarray,
    fill0: int,
    fill1: int,
    fill2: int,
) -> None:
    """Full-res horizontal nearest remap; OOB → fill. Numba parallel path."""
    dw, h = map_x.shape
    w = img.shape[0]
    for x in prange(dw):
        for y in range(h):
            mx = map_x[x, y]
            if mx < 0.0 or mx >= w:
                out[x, y, 0] = fill0
                out[x, y, 1] = fill1
                out[x, y, 2] = fill2
            else:
                xi = int(mx + 0.5)
                if xi < 0:
                    xi = 0
                if xi >= w:
                    xi = w - 1
                out[x, y, 0] = img[xi, y, 0]
                out[x, y, 1] = img[xi, y, 1]
                out[x, y, 2] = img[xi, y, 2]


def _warp_horizontal_nearest_numpy(
    img: np.ndarray,
    map_x: np.ndarray,
    *,
    fill: tuple[int, int, int],
) -> np.ndarray:
    """Full-res horizontal nearest remap (numpy fallback; no downscale blur)."""
    w = img.shape[0]
    valid = (map_x >= 0.0) & (map_x < float(w))
    xi = np.rint(np.clip(map_x, 0.0, w - 1.0)).astype(np.int32)
    # y index = column of map (broadcast rows).
    h = map_x.shape[1]
    gy = np.broadcast_to(np.arange(h, dtype=np.int32)[None, :], map_x.shape)
    out = img[xi, gy].copy()
    out[~valid] = np.asarray(fill, dtype=np.uint8)
    return out


def _resolve_shader(path: Path) -> Path:
    path = Path(path)
    if not path.is_absolute():
        candidates = [Path.cwd() / path, REPO_ROOT / path, SLANG_DIR / path.name]
        for c in candidates:
            if c.exists():
                return c.resolve()
    return path.resolve()


def hotswap_temp_path(shader: Path) -> Path:
    """Temp copy used for live compile — never the user's real shader path."""
    cache = ASSETS_DIR / "cache"
    return (cache / f"live_hotswap_{shader.stem}.slang").resolve()


def _entry_param_names(fn: Any) -> frozenset[str]:
    """Parameter names declared on a SlangPy-bound entry, or empty if unknown."""
    slang_func = getattr(fn, "_slang_func", None)
    if slang_func is None:
        return frozenset()
    try:
        return frozenset(p.name for p in slang_func.parameters)
    except Exception:  # noqa: BLE001
        return frozenset()


def _entry_accepts_time(fn: Any) -> bool:
    """True if the Slang entry declares a ``time`` parameter (seconds)."""
    return "time" in _entry_param_names(fn)


def _entry_accepts_mouse(fn: Any) -> bool:
    """True if the entry takes any mouse uniform (mouse / mouse_delta / mouse_down)."""
    names = _entry_param_names(fn)
    return bool(names & {"mouse", "mouse_delta", "mouse_down"})


def _param_type_full_name(param: Any) -> str:
    try:
        t = param.type
        return str(getattr(t, "full_name", "") or "") + " " + type(t).__name__
    except Exception:  # noqa: BLE001
        return ""


def _param_is_texture2d(param: Any) -> bool:
    blob = _param_type_full_name(param)
    return "Texture2D" in blob or (
        "TextureType" in blob and "Texture3D" not in blob and "TextureCube" not in blob
    )


def _param_is_sampler(param: Any) -> bool:
    blob = _param_type_full_name(param)
    return "SamplerState" in blob or "SamplerStateType" in blob


def _entry_texture_bindings(fn: Any) -> tuple[list[str], list[str]]:
    """Return (Texture2D param names, SamplerState param names) on the entry."""
    slang_func = getattr(fn, "_slang_func", None)
    if slang_func is None:
        return [], []
    tex: list[str] = []
    samp: list[str] = []
    try:
        for p in slang_func.parameters:
            name = str(p.name)
            if _param_is_texture2d(p):
                tex.append(name)
            elif _param_is_sampler(p):
                samp.append(name)
    except Exception:  # noqa: BLE001
        return [], []
    return tex, samp


def _load_image_rgba_f32(path: Path) -> np.ndarray:
    """Load image as HxWx4 float32 RGB[A] in [0,1] (adds opaque alpha if needed)."""
    from PIL import Image

    im = Image.open(path).convert("RGBA")
    arr = np.asarray(im, dtype=np.float32) * (1.0 / 255.0)
    return np.ascontiguousarray(arr)


def _numpy_sample_texture(
    rgba: np.ndarray,
    width: int,
    height: int,
    *,
    tint: tuple[float, float, float] = (1.0, 1.0, 1.0),
    flip_v: bool = True,
) -> np.ndarray:
    """CPU UV sample of an HxWx4 image into width×height RGB (matches SampleLevel + V flip)."""
    th, tw = int(rgba.shape[0]), int(rgba.shape[1])
    if th < 1 or tw < 1 or width < 1 or height < 1:
        return np.zeros((height, width, 3), dtype=np.float32)
    ys = (np.arange(height, dtype=np.float32) + 0.5) / float(height)
    xs = (np.arange(width, dtype=np.float32) + 0.5) / float(width)
    if flip_v:
        ys = 1.0 - ys
    fx = np.clip(xs * float(tw) - 0.5, 0.0, float(tw - 1))
    fy = np.clip(ys * float(th) - 0.5, 0.0, float(th - 1))
    x0 = np.floor(fx).astype(np.int32)
    y0 = np.floor(fy).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, tw - 1)
    y1 = np.clip(y0 + 1, 0, th - 1)
    tx = (fx - x0.astype(np.float32))[None, :]
    ty = (fy - y0.astype(np.float32))[:, None]
    yy0 = y0[:, None]
    yy1 = y1[:, None]
    xx0 = x0[None, :]
    xx1 = x1[None, :]
    c00 = rgba[yy0, xx0, :3]
    c10 = rgba[yy0, xx1, :3]
    c01 = rgba[yy1, xx0, :3]
    c11 = rgba[yy1, xx1, :3]
    top = c00 * (1.0 - tx)[..., None] + c10 * tx[..., None]
    bot = c01 * (1.0 - tx)[..., None] + c11 * tx[..., None]
    out = top * (1.0 - ty)[..., None] + bot * ty[..., None]
    return np.clip(
        out * np.asarray(tint, dtype=np.float32).reshape(1, 1, 3), 0.0, 1e3
    ).astype(np.float32)


class LessonTextures:
    """Curriculum / entry Texture2D + SamplerState bindings for ``render_frame``."""

    __slots__ = ("path", "_rgba", "_tex", "_samp", "_path_key")

    def __init__(self) -> None:
        self.path: Path | None = None
        self._rgba: np.ndarray | None = None
        self._tex: Any = None
        self._samp: Any = None
        self._path_key: str | None = None

    def set_path(self, path: Path | None) -> None:
        key = str(path.resolve()) if path is not None else None
        if key == self._path_key:
            return
        self.path = path.resolve() if path is not None else None
        self._path_key = key
        self._rgba = None
        self._tex = None
        self._samp = None

    def clear(self) -> None:
        self.set_path(None)

    def ensure_rgba(self) -> np.ndarray | None:
        if self.path is None or not self.path.is_file():
            return None
        if self._rgba is None:
            self._rgba = _load_image_rgba_f32(self.path)
        return self._rgba

    def ensure_gpu(self, spy: Any, device: Any) -> tuple[Any, Any] | None:
        rgba = self.ensure_rgba()
        if rgba is None:
            return None
        if self._tex is None or self._samp is None:
            h, w = int(rgba.shape[0]), int(rgba.shape[1])
            self._tex = device.create_texture(
                width=w,
                height=h,
                format=spy.Format.rgba32_float,
                usage=spy.TextureUsage.shader_resource,
                data=rgba,
            )
            self._samp = device.create_sampler(
                min_filter=spy.TextureFilteringMode.linear,
                mag_filter=spy.TextureFilteringMode.linear,
                mip_filter=spy.TextureFilteringMode.linear,
                address_u=spy.TextureAddressingMode.clamp_to_edge,
                address_v=spy.TextureAddressingMode.clamp_to_edge,
                address_w=spy.TextureAddressingMode.clamp_to_edge,
            )
        return self._tex, self._samp

    def spy_kwargs(self, fn: Any, spy: Any, device: Any) -> dict[str, Any]:
        tex_names, samp_names = _entry_texture_bindings(fn)
        if not tex_names and not samp_names:
            return {}
        gpu = self.ensure_gpu(spy, device)
        if gpu is None:
            return {}
        tex, samp = gpu
        out: dict[str, Any] = {}
        for name in tex_names:
            out[name] = tex
        for name in samp_names:
            out[name] = samp
        return out


def _default_texture_path() -> Path:
    return (REPO_ROOT / "labs" / "slang_playground" / "assets" / "cowboy_hat.png").resolve()


def _param_float_vec_len(param: Any) -> int | None:
    """Return 3 or 4 if ``param`` is float3/float4; else None."""
    try:
        t = param.type
        full = str(getattr(t, "full_name", "") or "")
        shape = list(getattr(t, "shape", []) or [])
        scalar = getattr(t, "scalar_type", None)
        scalar_name = str(getattr(scalar, "full_name", "") or "") if scalar is not None else ""
        if "float" not in full and scalar_name != "float":
            return None
        n = int(shape[0]) if shape else 0
        if n in (3, 4):
            return n
        # Fallback: parse vector<float,N>
        m = re.search(r"vector<\s*float\s*,\s*([34])\s*>", full)
        if m:
            return int(m.group(1))
    except Exception:  # noqa: BLE001
        return None
    return None


def _is_color_like_name(name: str) -> bool:
    """Heuristic: param name looks like a color uniform (not a position/normal)."""
    tokens = [t for t in re.split(r"[_\W]+", name.lower()) if t]
    if not tokens:
        return False
    has_hint = any(t in _COLOR_NAME_HINTS for t in tokens)
    if not has_hint:
        return False
    # e.g. light_dir / base_pos — spatial, not a swatch.
    has_exclude = any(t in _COLOR_NAME_EXCLUDE for t in tokens)
    if has_exclude and not any(
        t in {"color", "colour", "rgb", "col", "albedo", "tint", "emissive", "diffuse"}
        for t in tokens
    ):
        return False
    return True


def _entry_color_params(fn: Any) -> list[tuple[str, int]]:
    """Color-like float3/float4 params on the entry, in declaration order."""
    slang_func = getattr(fn, "_slang_func", None)
    if slang_func is None:
        return []
    out: list[tuple[str, int]] = []
    try:
        for p in slang_func.parameters:
            ncomp = _param_float_vec_len(p)
            if ncomp is None:
                continue
            name = str(p.name)
            if name in {"pixel", "resolution", "mouse", "mouse_delta"}:
                continue
            if _is_color_like_name(name):
                out.append((name, ncomp))
    except Exception:  # noqa: BLE001
        return []
    return out


def _default_color_rgba(name: str) -> list[float]:
    """Sensible default swatch for a newly discovered color uniform."""
    n = name.lower()
    presets = {
        "color_a": [0.95, 0.25, 0.20, 1.0],
        "colour_a": [0.95, 0.25, 0.20, 1.0],
        "color_b": [0.10, 0.35, 0.90, 1.0],
        "colour_b": [0.10, 0.35, 0.90, 1.0],
        "color": [0.30, 0.70, 0.55, 1.0],
        "colour": [0.30, 0.70, 0.55, 1.0],
        "albedo": [0.72, 0.62, 0.48, 1.0],
        "tint": [1.0, 1.0, 1.0, 1.0],
        "base": [0.55, 0.55, 0.58, 1.0],
        "base_color": [0.55, 0.55, 0.58, 1.0],
        "sky": [0.35, 0.55, 0.95, 1.0],
        "fog": [0.55, 0.65, 0.78, 1.0],
        "light": [1.0, 0.95, 0.85, 1.0],
        "emissive": [0.9, 0.45, 0.15, 1.0],
        "diffuse": [0.65, 0.65, 0.68, 1.0],
        "specular": [0.9, 0.9, 0.92, 1.0],
        "bg": [0.08, 0.09, 0.12, 1.0],
        "background": [0.08, 0.09, 0.12, 1.0],
    }
    if n in presets:
        return list(presets[n])
    if "tint" in n:
        return [1.0, 1.0, 1.0, 1.0]
    if "sky" in n:
        return [0.35, 0.55, 0.95, 1.0]
    if "fog" in n:
        return [0.55, 0.65, 0.78, 1.0]
    if "emissive" in n or "glow" in n:
        return [0.9, 0.45, 0.15, 1.0]
    if n.endswith("_a") or n.endswith("a"):
        return [0.95, 0.25, 0.20, 1.0]
    if n.endswith("_b") or n.endswith("b"):
        return [0.10, 0.35, 0.90, 1.0]
    return [0.30, 0.70, 0.55, 1.0]


def _rgb_to_hsv(r: float, g: float, b: float) -> tuple[float, float, float]:
    """RGB [0,1] → HSV with H in [0,1)."""
    mx = max(r, g, b)
    mn = min(r, g, b)
    d = mx - mn
    if d < 1e-8:
        h = 0.0
    elif mx == r:
        h = ((g - b) / d) % 6.0
    elif mx == g:
        h = (b - r) / d + 2.0
    else:
        h = (r - g) / d + 4.0
    h /= 6.0
    s = 0.0 if mx < 1e-8 else d / mx
    return h, s, mx


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    """HSV (H in [0,1)) → RGB [0,1]."""
    h = h % 1.0
    if s <= 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i %= 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    return v, p, q


class ColorUniforms:
    """Live color uniforms discovered on the Slang entry + picker UI state."""

    __slots__ = ("params", "values", "focus", "drag", "_sv_cache_key", "_sv_surf", "_hue_surf")

    def __init__(self) -> None:
        self.params: list[tuple[str, int]] = []
        self.values: dict[str, list[float]] = {}
        self.focus: int = 0
        self.drag: str | None = None  # sv | hue | r | g | b | a
        self._sv_cache_key: float | None = None
        self._sv_surf: Any = None
        self._hue_surf: Any = None

    @property
    def active(self) -> bool:
        return bool(self.params)

    def sync(self, fn: Any) -> list[str]:
        """Refresh from entry; return newly discovered param names."""
        discovered = _entry_color_params(fn)
        old_names = {n for n, _ in self.params}
        self.params = discovered
        new_names: list[str] = []
        keep = {n for n, _ in discovered}
        for n in list(self.values.keys()):
            if n not in keep:
                del self.values[n]
        for name, ncomp in discovered:
            if name not in self.values:
                rgba = _default_color_rgba(name)
                if ncomp == 3:
                    rgba[3] = 1.0
                self.values[name] = rgba
                if name not in old_names:
                    new_names.append(name)
        if self.focus >= len(self.params):
            self.focus = max(0, len(self.params) - 1)
        self.drag = None
        return new_names

    def clear(self) -> None:
        self.params = []
        self.values.clear()
        self.focus = 0
        self.drag = None

    def current_name(self) -> str | None:
        if not self.params:
            return None
        return self.params[self.focus][0]

    def current_ncomp(self) -> int:
        if not self.params:
            return 3
        return self.params[self.focus][1]

    def current_rgba(self) -> list[float]:
        name = self.current_name()
        if name is None:
            return [0.3, 0.7, 0.55, 1.0]
        return self.values.setdefault(name, _default_color_rgba(name))

    def set_rgb(self, r: float, g: float, b: float) -> None:
        rgba = self.current_rgba()
        rgba[0] = min(1.0, max(0.0, float(r)))
        rgba[1] = min(1.0, max(0.0, float(g)))
        rgba[2] = min(1.0, max(0.0, float(b)))

    def set_channel(self, ch: int, v: float) -> None:
        rgba = self.current_rgba()
        if 0 <= ch < 4:
            rgba[ch] = min(1.0, max(0.0, float(v)))

    def cycle_focus(self, delta: int = 1) -> None:
        if not self.params:
            return
        self.focus = (self.focus + delta) % len(self.params)
        self.drag = None

    def select_index(self, i: int) -> None:
        if 0 <= i < len(self.params):
            self.focus = i
            self.drag = None

    def select_name(self, name: str) -> bool:
        key = name.lower()
        for i, (n, _) in enumerate(self.params):
            if n.lower() == key:
                self.select_index(i)
                return True
        return False

    def spy_kwargs(self, spy: Any) -> dict[str, Any]:
        """Build slangpy float3/float4 kwargs for ``render_frame``."""
        out: dict[str, Any] = {}
        for name, ncomp in self.params:
            rgba = self.values.get(name) or _default_color_rgba(name)
            if ncomp >= 4:
                out[name] = spy.float4(
                    float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3])
                )
            else:
                out[name] = spy.float3(float(rgba[0]), float(rgba[1]), float(rgba[2]))
        return out


def _focus_color_from_token(
    colors: ColorUniforms,
    word: str,
    line: str,
    col_start: int,
) -> bool:
    """Focus Color panel from an editor token. Returns True if focus changed."""
    if not colors.active or not word:
        return False
    prev = colors.focus
    if colors.select_name(word):
        return colors.focus != prev
    low = word.lower()
    if low in {"float3", "float4"}:
        rest = line[col_start + len(word) :]
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", rest)
        if m and colors.select_name(m.group(1)):
            return colors.focus != prev
        # Type alone → first color picker (reveal / focus panel).
        if colors.params:
            colors.select_index(0)
            return colors.focus != prev
    return False


def render_frame(
    module: Any,
    entry: str,
    width: int,
    height: int,
    time_s: float = 0.0,
    *,
    mouse: tuple[float, float] = (0.0, 0.0),
    mouse_delta: tuple[float, float] = (0.0, 0.0),
    mouse_down: int = 0,
    colors: ColorUniforms | None = None,
    textures: LessonTextures | None = None,
) -> np.ndarray:
    """Call entry(pixel, resolution[, time][, mouse…][, colors…][, tex…]) -> float3.

    Always resolves the entry fresh and allocates a new output Tensor so nothing
    from a previous module generation is reused.

    If the entry declares ``float time``, passes ``time_s`` (seconds since start
    in live mode). Optional ``float2 mouse`` (pixel coords, top-left origin),
    ``float2 mouse_delta``, and ``int mouse_down`` match ShaderToy-style look input.
    Color-like ``float3`` / ``float4`` params from ``colors`` are passed when present.
    ``Texture2D`` / ``SamplerState`` params bind from ``textures`` (curriculum asset).
    If GPU texture dispatch fails, falls back to numpy UV sampling of the same image.
    """
    import slangpy as spy

    device = get_device()
    fn = getattr(module, entry)
    out = spy.Tensor.empty(device, shape=(height, width), dtype=spy.float3)
    names = _entry_param_names(fn)
    kwargs: dict[str, Any] = {
        "pixel": spy.call_id(),
        "resolution": spy.int2(width, height),
        "_result": out,
    }
    if "time" in names:
        kwargs["time"] = float(time_s)
    if "mouse" in names:
        kwargs["mouse"] = spy.float2(float(mouse[0]), float(mouse[1]))
    if "mouse_delta" in names:
        kwargs["mouse_delta"] = spy.float2(float(mouse_delta[0]), float(mouse_delta[1]))
    if "mouse_down" in names:
        kwargs["mouse_down"] = int(mouse_down)
    if colors is not None and colors.active:
        for k, v in colors.spy_kwargs(spy).items():
            if k in names:
                kwargs[k] = v
    else:
        # Headless / --once: still satisfy required color-like params with defaults.
        for name, ncomp in _entry_color_params(fn):
            if name not in names:
                continue
            rgba = _default_color_rgba(name)
            if ncomp >= 4:
                kwargs[name] = spy.float4(
                    float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3])
                )
            else:
                kwargs[name] = spy.float3(
                    float(rgba[0]), float(rgba[1]), float(rgba[2])
                )

    tex_names, samp_names = _entry_texture_bindings(fn)
    needs_tex = bool(tex_names or samp_names)
    tex_bundle = textures
    if needs_tex and tex_bundle is None:
        tex_bundle = LessonTextures()
        tex_bundle.set_path(_default_texture_path())
    if needs_tex and tex_bundle is not None:
        if tex_bundle.path is None:
            tex_bundle.set_path(_default_texture_path())
        for k, v in tex_bundle.spy_kwargs(fn, spy, device).items():
            if k in names:
                kwargs[k] = v

    try:
        fn(**kwargs)
        return np.asarray(out.to_numpy(), dtype=np.float32)
    except Exception:
        if not needs_tex or tex_bundle is None:
            raise
        rgba = tex_bundle.ensure_rgba()
        if rgba is None:
            raise
        tint = (1.0, 1.0, 1.0)
        if colors is not None and colors.active:
            name = colors.current_name()
            if name is not None:
                c = colors.values.get(name) or _default_color_rgba(name)
                tint = (float(c[0]), float(c[1]), float(c[2]))
        else:
            for name, _ncomp in _entry_color_params(fn):
                c = _default_color_rgba(name)
                tint = (float(c[0]), float(c[1]), float(c[2]))
                break
        return _numpy_sample_texture(rgba, width, height, tint=tint, flip_v=False)


def _map_pos_to_shader_mouse(
    pos: tuple[int, int],
    img_rect: Any,
    width: int,
    height: int,
) -> tuple[float, float]:
    """Map window coords onto shader pixel space (top-left origin, matches ``pixel``)."""
    if img_rect is None or not getattr(img_rect, "width", 0) or not img_rect.height:
        return 0.0, 0.0
    lx = (float(pos[0]) - float(img_rect.x)) / float(max(1, img_rect.width))
    ly = (float(pos[1]) - float(img_rect.y)) / float(max(1, img_rect.height))
    lx = min(1.0, max(0.0, lx))
    ly = min(1.0, max(0.0, ly))
    return lx * float(width), ly * float(height)


def _to_uint8_rgb(img: np.ndarray) -> np.ndarray:
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)


def load_shader(shader: Path) -> Any:
    """Recompile shader from disk (fresh session module name each call)."""
    clear_module_cache()
    return load_module_from_path(
        shader,
        search_paths=[SLANG_DIR, shader.parent],
        fresh=True,
    )


def run_once(
    shader: Path,
    entry: str,
    width: int,
    height: int,
    out: Path | None = None,
    time_s: float = 0.0,
    *,
    mouse: tuple[float, float] = (0.0, 0.0),
    mouse_delta: tuple[float, float] = (0.0, 0.0),
    mouse_down: int = 0,
    texture: Path | None = None,
) -> np.ndarray:
    """Compile, render one frame, optionally write a PNG. For smoke / headless."""
    get_device()
    module = load_shader(shader)
    textures: LessonTextures | None = None
    if texture is not None:
        textures = LessonTextures()
        textures.set_path(texture)
    img = render_frame(
        module,
        entry,
        width,
        height,
        time_s=time_s,
        mouse=mouse,
        mouse_delta=mouse_delta,
        mouse_down=mouse_down,
        textures=textures,
    )
    if out is not None:
        from PIL import Image

        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(_to_uint8_rgb(img), mode="RGB").save(out)
        print(f"Wrote {out}")
    return img


def _read_shader_source(shader: Path) -> str:
    try:
        return shader.read_text(encoding="utf-8")
    except OSError as exc:
        return f"// could not read {shader.name}: {exc}"


def _code_line_height(font: Any) -> int:
    """Monospace row pitch: glyph height + leading (never tighter than SysFont linesize)."""
    return max(int(font.get_linesize()), int(font.get_height()) + _CODE_LINE_GAP)


def _console_line_height(font: Any) -> int:
    """Console row pitch — same idea as code, slightly tighter leading."""
    return max(int(font.get_linesize()), int(font.get_height()) + _CONSOLE_LINE_GAP)


def _light_sharpen_rgb(rgb: np.ndarray, amount: float = _PRESENT_SHARPEN) -> np.ndarray:
    """Cheap present-path unsharp mask (uint8 HxWx3). Skips if amount ~= 0."""
    if amount <= 1e-6 or rgb.size == 0 or rgb.shape[0] < 3 or rgb.shape[1] < 3:
        return rgb
    f = rgb.astype(np.float32)
    blur = f.copy()
    # 3x3 box (center + 8 neighbors) — cheap, no SciPy.
    blur[1:-1, 1:-1] = (
        f[:-2, :-2]
        + f[:-2, 1:-1]
        + f[:-2, 2:]
        + f[1:-1, :-2]
        + f[1:-1, 1:-1]
        + f[1:-1, 2:]
        + f[2:, :-2]
        + f[2:, 1:-1]
        + f[2:, 2:]
    ) * (1.0 / 9.0)
    out = f + float(amount) * (f - blur)
    return np.clip(out, 0, 255).astype(np.uint8)


def _render_hires_text(
    pygame: Any,
    font_hi: Any,
    text: str,
    color: tuple[int, int, int],
    *,
    scale: int = _LABEL_AA_SCALE,
) -> Any:
    """Render AA text at ``scale``x then smoothscale down for sharper UI labels."""
    if not text:
        return font_hi.render("", True, color)
    big = font_hi.render(text, True, color)
    if scale <= 1:
        return big
    w = max(1, int(round(big.get_width() / float(scale))))
    h = max(1, int(round(big.get_height() / float(scale))))
    return pygame.transform.smoothscale(big, (w, h))


def _classify_ident(name: str) -> str:
    if name in _SLANG_KEYWORDS:
        return "keyword"
    if name in _SLANG_TYPES or re.fullmatch(r"(?:float|int|uint|bool|half|double)\d(?:x\d)?", name):
        return "type"
    return "ident"


def tokenize_slang_line(line: str, in_block: bool) -> tuple[list[tuple[str, str]], bool]:
    """Lightweight Slang tokenizer for one line. Returns (tokens, still_in_block_comment)."""
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(line)

    while i < n:
        if in_block:
            end = line.find("*/", i)
            if end < 0:
                tokens.append((line[i:], "comment"))
                return tokens, True
            tokens.append((line[i : end + 2], "comment"))
            i = end + 2
            in_block = False
            continue

        ch = line[i]
        if ch in " \t":
            j = i + 1
            while j < n and line[j] in " \t":
                j += 1
            tokens.append((line[i:j], "default"))
            i = j
            continue

        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            tokens.append((line[i:], "comment"))
            break

        if ch == "/" and i + 1 < n and line[i + 1] == "*":
            end = line.find("*/", i + 2)
            if end < 0:
                tokens.append((line[i:], "comment"))
                return tokens, True
            tokens.append((line[i : end + 2], "comment"))
            i = end + 2
            continue

        if ch == "[":
            end = line.find("]", i + 1)
            if end >= 0:
                tokens.append((line[i : end + 1], "attr"))
                i = end + 1
                continue
            tokens.append((ch, "default"))
            i += 1
            continue

        if ch in "\"'":
            quote = ch
            j = i + 1
            while j < n:
                if line[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if line[j] == quote:
                    j += 1
                    break
                j += 1
            tokens.append((line[i:j], "string"))
            i = j
            continue

        if ch.isdigit() or (ch == "." and i + 1 < n and line[i + 1].isdigit()):
            j = i + 1
            while j < n and (line[j].isalnum() or line[j] in ".xX'"):
                j += 1
            tokens.append((line[i:j], "number"))
            i = j
            continue

        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < n and (line[j].isalnum() or line[j] == "_"):
                j += 1
            word = line[i:j]
            tokens.append((word, _classify_ident(word)))
            i = j
            continue

        tokens.append((ch, "default"))
        i += 1

    return tokens, in_block


def tokenize_slang(source: str) -> list[list[tuple[str, str]]]:
    """Tokenize full source into per-line (text, kind) lists."""
    lines = source.replace("\t", "    ").splitlines() or [""]
    out: list[list[tuple[str, str]]] = []
    in_block = False
    for line in lines:
        toks, in_block = tokenize_slang_line(line, in_block)
        out.append(toks if toks else [("", "default")])
    return out


# Editor highlighting (avoids circular import with code_editor).
CodeEditor._tokenize_fn = tokenize_slang


def _max_scroll(n_lines: int, line_h: int, view_h: int, pad: int = 0) -> int:
    content_h = n_lines * line_h + 2 * pad
    return max(0, content_h - view_h)


def _max_scroll_x(lines: list[str], font: Any, view_w: int) -> int:
    if view_w <= 0:
        return 0
    max_w = 0
    for line in lines:
        max_w = max(max_w, font.size(line)[0])
    # Room for caret past the last glyph.
    caret = max(6, font.size("M")[0])
    return max(0, max_w + caret - view_w)


def _draw_code_panel(
    target: Any,
    pygame: Any,
    font: Any,
    editor: CodeEditor,
    rect: Any,
    *,
    caret_on: bool,
) -> None:
    """Editable side code panel with syntax colors, selection, + caret.

    Text is laid out inside a padded inset with correct monospace line pitch.
    Clip is the inset so glyphs/caret are never cut by the panel edge; long
    lines scroll horizontally instead of truncating mid-token.
    """
    if rect.width <= 0 or rect.height <= 0:
        return
    pygame.draw.rect(target, _CODE_BG, rect)

    pad = _PANEL_PAD
    inner = pygame.Rect(
        rect.x + pad,
        rect.y + pad,
        max(1, rect.width - 2 * pad),
        max(1, rect.height - 2 * pad),
    )
    line_h = _code_line_height(font)
    glyph_h = font.get_height()
    # Vertically center glyphs within the line cell.
    glyph_oy = max(0, (line_h - glyph_h) // 2)

    clip = target.get_clip()
    target.set_clip(inner)

    sel = editor.selection_range()
    y = inner.y - editor.scroll_y
    token_lines = editor._tokens

    for row, tokens in enumerate(token_lines):
        if y + line_h < inner.y:
            y += line_h
            continue
        if y > inner.bottom:
            break
        line_text = editor.lines[row] if row < len(editor.lines) else ""

        # Selection background for this row.
        if sel is not None:
            r0, c0, r1, c1 = sel
            if r0 <= row <= r1:
                sc = c0 if row == r0 else 0
                ec = c1 if row == r1 else len(line_text)
                if row < r1 and r0 != r1:
                    # Full-line select includes a trailing "newline" gutter.
                    x0 = inner.x - editor.scroll_x + font.size(line_text[:sc])[0]
                    x1 = inner.x - editor.scroll_x + font.size(line_text)[0] + font.size(" ")[0]
                else:
                    x0 = inner.x - editor.scroll_x + font.size(line_text[:sc])[0]
                    x1 = inner.x - editor.scroll_x + font.size(line_text[:ec])[0]
                if x1 < x0:
                    x0, x1 = x1, x0
                if x1 > inner.x and x0 < inner.right:
                    pygame.draw.rect(
                        target,
                        _SEL_BG,
                        pygame.Rect(
                            max(inner.x, x0),
                            y,
                            max(1, min(inner.right, x1) - max(inner.x, x0)),
                            line_h,
                        ),
                    )

        x = inner.x - editor.scroll_x
        for text, kind in tokens:
            if not text:
                continue
            # Skip tokens fully left of the viewport; stop once past the right.
            tw = font.size(text)[0]
            if x + tw < inner.x:
                x += tw
                continue
            if x > inner.right:
                break
            color = _TOKEN_COLORS.get(kind, _TOKEN_COLORS["default"])
            surf = font.render(text, True, color)
            target.blit(surf, (x, y + glyph_oy))
            x += surf.get_width()

        if editor.focused and caret_on and row == editor.row and not editor.has_selection():
            prefix = line_text[: editor.col]
            cx = inner.x - editor.scroll_x + font.size(prefix)[0]
            if inner.left - 1 <= cx <= inner.right:
                cy0 = y + glyph_oy
                cy1 = cy0 + max(1, glyph_h - 1)
                pygame.draw.line(target, _CARET, (cx, cy0), (cx, cy1), 1)
        y += line_h

    target.set_clip(clip)


def _draw_bevel_rect(
    target: Any,
    pygame: Any,
    rect: Any,
    *,
    inset: bool = False,
    thickness: int = _CHROME,
    corner_r: int = 0,
    specular: bool = True,
) -> None:
    """Raised/inset metal bevel. Raised: light TL / dark BR; inset flips.

    When ``corner_r`` > 0, bevel strokes stop short of the corners so a rounded
    outer silhouette doesn't show hard square chrome. Optional specular hairline
    on the outer light edge for a glass/metal read.
    """
    if rect.width <= 0 or rect.height <= 0 or thickness <= 0:
        return
    light = _BEVEL_DARK if inset else _BEVEL_LIGHT
    dark = _BEVEL_LIGHT if inset else _BEVEL_DARK
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    cr = max(0, min(int(corner_r), w // 2, h // 2))
    for i in range(thickness):
        # Inset endpoints away from corners when rounding.
        pad = max(0, cr - i)
        x0, y0 = x + i, y + i
        x1, y1 = x + w - 1 - i, y + h - 1 - i
        # Top + left (light when raised)
        pygame.draw.line(target, light, (x0 + pad, y0), (x1 - pad, y0), 1)
        pygame.draw.line(target, light, (x0, y0 + pad), (x0, y1 - pad), 1)
        # Bottom + right (dark when raised)
        pygame.draw.line(target, dark, (x0 + pad, y1), (x1 - pad, y1), 1)
        pygame.draw.line(target, dark, (x1, y0 + pad), (x1, y1 - pad), 1)
        if pad > 0:
            # Soft arc hints at the four corners (single-pixel polyline).
            _draw_corner_bevel_arcs(
                target, pygame, x0, y0, x1, y1, pad, light, dark
            )
    if specular and not inset and thickness >= 1:
        # Soft inner specular hairline — muted glass/metal highlight.
        i = 0
        pad = max(0, cr - i)
        x0, y0 = x + i + 1, y + i + 1
        x1 = x + w - 2 - i
        # Two-tone soft highlight (spec + slightly dimmer second pixel).
        pygame.draw.line(target, _BEVEL_SPEC, (x0 + pad, y0), (x1 - pad, y0), 1)
        if h > 4:
            dim = tuple(max(0, c - 28) for c in _BEVEL_SPEC)
            pygame.draw.line(target, dim, (x0 + pad, y0 + 1), (x1 - pad, y0 + 1), 1)


def _hsv_to_rgb8(h: float, s: float, v: float) -> tuple[int, int, int]:
    """h in [0,1), s/v in [0,1] → 8-bit RGB for pygame blits."""
    r, g, b = _hsv_to_rgb(h, s, v)
    return (
        int(max(0, min(255, round(r * 255)))),
        int(max(0, min(255, round(g * 255)))),
        int(max(0, min(255, round(b * 255)))),
    )


def _draw_frosted_title_bar(target: Any, pygame: Any, rect: Any) -> None:
    """Fake glassmorphism: dark base + smooth vertical frost gradient + sheen."""
    if rect.width <= 0 or rect.height <= 0:
        return
    pygame.draw.rect(target, _TITLE_FACE, rect)
    glass = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    h = max(1, rect.height)
    # Three-stop smoothstep blend (less banding than linear mid hinge).
    for y in range(h):
        t = y / float(h - 1) if h > 1 else 0.0
        # Smoothstep for softer glass falloff.
        s = t * t * (3.0 - 2.0 * t)
        if s < 0.42:
            u = s / 0.42
            c0, c1 = _TITLE_GLASS_TOP, _TITLE_GLASS_MID
        else:
            u = (s - 0.42) / 0.58
            u = u * u * (3.0 - 2.0 * u)
            c0, c1 = _TITLE_GLASS_MID, _TITLE_GLASS_BOT
        rgba = tuple(int(c0[i] + (c1[i] - c0[i]) * u) for i in range(4))
        pygame.draw.line(glass, rgba, (0, y), (rect.width, y))
    # Soft horizontal sheen band (frost highlight) — wider, lower alpha.
    sheen_y = max(2, h // 3)
    for y in range(sheen_y):
        a = int(36 * (1.0 - y / float(sheen_y)) ** 1.4)
        pygame.draw.line(glass, (255, 255, 255, a), (0, y), (rect.width, y))
    target.blit(glass, rect.topleft)
    # Soft top rim + bottom hairline separator.
    pygame.draw.line(
        target,
        (255, 255, 255, 28) if target.get_flags() & pygame.SRCALPHA else (120, 128, 142),
        (rect.x + 1, rect.y),
        (rect.right - 2, rect.y),
        1,
    )
    pygame.draw.line(
        target,
        (255, 255, 255, 36) if target.get_flags() & pygame.SRCALPHA else (78, 86, 100),
        (rect.x, rect.bottom - 1),
        (rect.right, rect.bottom - 1),
        1,
    )


def _draw_traffic_lights(
    target: Any,
    pygame: Any,
    title_rect: Any,
    *,
    close_pressed: bool = False,
) -> tuple[Any, Any, Any, Any]:
    """Traffic beads: close / amber / window-FS / shader-FS. Returns hit rects."""
    empty = pygame.Rect(0, 0, 0, 0)
    if title_rect.width <= 0:
        return empty, empty, empty, empty
    cy = title_rect.y + title_rect.height // 2
    x0 = title_rect.x + _TRAFFIC_PAD_X + _TRAFFIC_R
    colors = (
        (_TRAFFIC_RED, _TRAFFIC_RED_RIM),
        (_TRAFFIC_YELLOW, _TRAFFIC_YELLOW_RIM),
        (_TRAFFIC_GREEN, _TRAFFIC_GREEN_RIM),
        (_TRAFFIC_CYAN, _TRAFFIC_CYAN_RIM),
    )
    rects: list[Any] = []
    for i, (face, rim) in enumerate(colors):
        cx = x0 + i * (_TRAFFIC_R * 2 + _TRAFFIC_GAP)
        r = _TRAFFIC_R + (1 if i == 0 and close_pressed else 0)
        hit = pygame.Rect(cx - _TRAFFIC_R - 2, cy - _TRAFFIC_R - 2, _TRAFFIC_R * 2 + 4, _TRAFFIC_R * 2 + 4)
        rects.append(hit)
        # Soft drop shadow under the bead.
        pygame.draw.circle(target, (12, 14, 18), (cx, cy + 1), r + 1)
        pygame.draw.circle(target, rim, (cx, cy), r + 1)
        pygame.draw.circle(target, face, (cx, cy), r)
        # Soft specular glint (smaller, offset NW).
        glint = max(1, r // 3)
        pygame.draw.circle(target, (255, 255, 255), (cx - 2, cy - 2), glint)
        # Inner rim darken for depth.
        pygame.draw.circle(target, rim, (cx, cy), r, 1)
    return rects[0], rects[1], rects[2], rects[3]


def _draw_iridescent_title(
    target: Any,
    pygame: Any,
    font: Any,
    text: str,
    x: int,
    y: int,
    *,
    phase: float = 0.0,
    font_hi: Any | None = None,
) -> Any:
    """Classic embossed title with a subtle iridescent rim; 2x→smoothscale AA."""
    if not text:
        return font.render("", True, _TITLE_TEXT)

    def _glyph(col: tuple[int, int, int]) -> Any:
        if font_hi is not None:
            return _render_hires_text(pygame, font_hi, text, col)
        return font.render(text, True, col)

    # Subtle iridescent outline (low sat/value so it doesn't wash out the face).
    offsets = (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (1, -1),
        (-1, 1),
        (1, 1),
    )
    for i, (ox, oy) in enumerate(offsets):
        hue = (phase + i * 0.09) % 1.0
        col = _hsv_to_rgb8(hue, 0.22, 0.42)
        target.blit(_glyph(col), (x + ox, y + oy))
    # Classic emboss: dark shadow down-right, light highlight up-left, mid face.
    target.blit(_glyph(_TITLE_EMBOSS_DARK), (x + 1, y + 1))
    target.blit(_glyph(_TITLE_EMBOSS_LIGHT), (x - 1, y - 1))
    body = _glyph(_TITLE_TEXT)
    target.blit(body, (x, y))
    return body


def _traffic_cluster_width() -> int:
    n = _TRAFFIC_COUNT
    return _TRAFFIC_PAD_X + n * (_TRAFFIC_R * 2) + (n - 1) * _TRAFFIC_GAP + 12


def _desktop_size(pygame: Any) -> tuple[int, int]:
    """Best-effort desktop resolution for fullscreen modes."""
    try:
        info = pygame.display.Info()
        w, h = int(info.current_w), int(info.current_h)
        if w > 0 and h > 0:
            return w, h
    except Exception:  # noqa: BLE001
        pass
    return 1920, 1080


def _draw_corner_bevel_arcs(
    target: Any,
    pygame: Any,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    r: int,
    light: tuple[int, int, int],
    dark: tuple[int, int, int],
) -> None:
    """Approximate rounded bevel corners with short polylines."""
    if r <= 1:
        return
    steps = max(4, min(12, r * 2))  # denser arcs = less chunky corner pixels
    for i in range(steps + 1):
        a0 = (math.pi * i) / (2 * steps)
        a1 = (math.pi * (i + 1)) / (2 * steps) if i < steps else a0
        # Top-left (light): from top edge into left edge.
        p0 = (int(round(x0 + r * (1.0 - math.cos(a0)))), int(round(y0 + r * (1.0 - math.sin(a0)))))
        p1 = (int(round(x0 + r * (1.0 - math.cos(a1)))), int(round(y0 + r * (1.0 - math.sin(a1)))))
        if i < steps:
            pygame.draw.line(target, light, p0, p1, 1)
        # Top-right (light→dark blend on top; use light for upper arc)
        p0 = (int(round(x1 - r * (1.0 - math.cos(a0)))), int(round(y0 + r * (1.0 - math.sin(a0)))))
        p1 = (int(round(x1 - r * (1.0 - math.cos(a1)))), int(round(y0 + r * (1.0 - math.sin(a1)))))
        if i < steps:
            pygame.draw.line(target, light if a0 < math.pi / 4 else dark, p0, p1, 1)
        # Bottom-left
        p0 = (int(round(x0 + r * (1.0 - math.cos(a0)))), int(round(y1 - r * (1.0 - math.sin(a0)))))
        p1 = (int(round(x0 + r * (1.0 - math.cos(a1)))), int(round(y1 - r * (1.0 - math.sin(a1)))))
        if i < steps:
            pygame.draw.line(target, light if a0 < math.pi / 4 else dark, p0, p1, 1)
        # Bottom-right (dark)
        p0 = (int(round(x1 - r * (1.0 - math.cos(a0)))), int(round(y1 - r * (1.0 - math.sin(a0)))))
        p1 = (int(round(x1 - r * (1.0 - math.cos(a1)))), int(round(y1 - r * (1.0 - math.sin(a1)))))
        if i < steps:
            pygame.draw.line(target, dark, p0, p1, 1)


def _mask_round_corners(
    target: Any,
    pygame: Any,
    w: int,
    h: int,
    radius: int,
    fill: tuple[int, int, int],
) -> None:
    """Fill pixels outside a rounded rect so sharp chrome corners don't read as boxes."""
    r = max(0, min(int(radius), w // 2, h // 2))
    if r <= 1:
        return
    rr = r * r
    # Top-left / top-right / bottom-left / bottom-right
    for i in range(r):
        for j in range(r):
            dx_l = r - 1 - i
            dy_t = r - 1 - j
            if dx_l * dx_l + dy_t * dy_t <= rr:
                continue
            # Outside quarter-circle in the corner square.
            target.set_at((i, j), fill)  # TL
            target.set_at((w - 1 - i, j), fill)  # TR
            target.set_at((i, h - 1 - j), fill)  # BL
            target.set_at((w - 1 - i, h - 1 - j), fill)  # BR


def _draw_button(
    target: Any,
    pygame: Any,
    font: Any,
    rect: Any,
    label: str,
    *,
    pressed: bool = False,
) -> None:
    if rect.width <= 0 or rect.height <= 0:
        return
    pygame.draw.rect(target, _BTN_FACE, rect)
    _draw_bevel_rect(target, pygame, rect, inset=pressed, thickness=1, specular=False)
    # Soft raised rim (less chunky than thick bevel).
    if not pressed:
        pygame.draw.line(
            target, _BEVEL_LIGHT, (rect.x + 1, rect.y), (rect.right - 2, rect.y), 1
        )
        pygame.draw.line(
            target, _BEVEL_DARK, (rect.x + 1, rect.bottom - 1), (rect.right - 2, rect.bottom - 1), 1
        )
    surf = font.render(label, True, _BTN_LABEL)
    tx = rect.x + (rect.width - surf.get_width()) // 2
    ty = rect.y + (rect.height - surf.get_height()) // 2 + (1 if pressed else 0)
    target.blit(surf, (tx, ty))


def _draw_bevel_h_divider(
    target: Any,
    pygame: Any,
    x: int,
    y: int,
    width: int,
    thickness: int = _DIVIDER,
    *,
    inset: bool = True,
) -> None:
    """Horizontal embossed bar (divider between content and console)."""
    if width <= 0 or thickness <= 0:
        return
    pygame.draw.rect(target, _BEVEL_FACE, (x, y, width, thickness))
    light = _BEVEL_DARK if inset else _BEVEL_LIGHT
    dark = _BEVEL_LIGHT if inset else _BEVEL_DARK
    pygame.draw.line(target, light, (x, y), (x + width - 1, y), 1)
    pygame.draw.line(
        target, dark, (x, y + thickness - 1), (x + width - 1, y + thickness - 1), 1
    )


def _draw_bevel_v_divider(
    target: Any,
    pygame: Any,
    x: int,
    y: int,
    height: int,
    thickness: int = _DIVIDER,
    *,
    inset: bool = True,
) -> None:
    """Vertical embossed bar (divider between shader and code panel)."""
    if height <= 0 or thickness <= 0:
        return
    pygame.draw.rect(target, _BEVEL_FACE, (x, y, thickness, height))
    light = _BEVEL_DARK if inset else _BEVEL_LIGHT
    dark = _BEVEL_LIGHT if inset else _BEVEL_DARK
    pygame.draw.line(target, light, (x, y), (x, y + height - 1), 1)
    pygame.draw.line(
        target, dark, (x + thickness - 1, y), (x + thickness - 1, y + height - 1), 1
    )


def _window_client_size(
    shader_w: int,
    shader_h: int,
    *,
    title_bar: bool = False,
) -> tuple[int, int]:
    """Default client = title? + chrome + two squares (shader | code) + console."""
    sw = max(shader_w, _SHADER_VIEW_MIN)
    sh = max(shader_h, _SHADER_VIEW_MIN)
    # Code column is a square matching the shader row height (e.g. --size 640 → 640).
    code_w = sh
    win_w = _CHROME + sw + _DIVIDER + code_w + _CHROME
    win_h = (
        _CHROME
        + sh
        + _DIVIDER
        + _LESSON_STRIP_H
        + _DIVIDER
        + _CONSOLE_H
        + _CHROME
    )
    if title_bar:
        win_h += _TITLE_BAR_H
    return win_w, win_h


def _min_window_client_size(*, title_bar: bool = False) -> tuple[int, int]:
    win_w = _CHROME + _SHADER_VIEW_MIN + _DIVIDER + _CODE_PANEL_MIN_W + _CHROME
    win_h = (
        _CHROME
        + _SHADER_VIEW_MIN
        + _DIVIDER
        + _LESSON_STRIP_H
        + _DIVIDER
        + _CONSOLE_H
        + _CHROME
    )
    if title_bar:
        win_h += _TITLE_BAR_H
    return win_w, win_h


def _draw_lesson_strip(
    target: Any,
    pygame: Any,
    font: Any,
    rect: Any,
    lines: list[str],
) -> None:
    """Populate the environment with the active example's explanation."""
    if rect.width <= 0 or rect.height <= 0:
        return
    pygame.draw.rect(target, _LESSON_BG, rect)
    y = rect.y + 6
    pad_x = rect.x + _PANEL_PAD
    max_w = max(40, rect.width - 2 * _PANEL_PAD)
    for i, raw in enumerate(lines[:4]):
        color = _LESSON_TITLE if i == 0 else _LESSON_BODY
        text = raw
        # Ellipsize long lines to fit the strip.
        while font.size(text)[0] > max_w and len(text) > 8:
            text = text[:-2]
        if text != raw and len(text) > 3:
            text = text[:-1] + "…"
        surf = font.render(text, True, color)
        target.blit(surf, (pad_x, y))
        y += surf.get_height() + 2
        if y > rect.bottom - 4:
            break


def _color_panel_layout(
    rect: Any,
    colors: ColorUniforms,
    pygame: Any,
    *,
    label_w: int = 120,
) -> dict[str, Any]:
    """Compute hit regions inside the Color panel (absolute coords)."""
    empty = pygame.Rect(0, 0, 0, 0)
    if rect.width <= 0 or rect.height <= 0 or not colors.active:
        return {
            "swatches": [],
            "sv": empty,
            "hue": empty,
            "sliders": [],
        }
    pad = 8
    x0 = rect.x + pad
    y0 = rect.y + pad
    sw = 22
    gap = 5
    # Swatches start after the "Color  name" label.
    sx = x0 + label_w
    swatches: list[tuple[int, Any]] = []
    for i, _ in enumerate(colors.params):
        swatches.append((i, pygame.Rect(sx, y0, sw, sw)))
        sx += sw + gap
    sq = min(72, rect.height - 2 * pad)
    hue_w = 14
    right = rect.right - pad
    hue = pygame.Rect(right - hue_w, y0, hue_w, sq)
    sv = pygame.Rect(hue.x - 6 - sq, y0, sq, sq)
    slider_x = x0 + 14
    slider_w = max(48, sv.x - 16 - slider_x)
    slider_y = y0 + sw + 10
    ncomp = colors.current_ncomp()
    n_sliders = 4 if ncomp >= 4 else 3
    sh = 10
    sliders: list[tuple[str, Any]] = []
    for i, ch in enumerate(("r", "g", "b", "a")[:n_sliders]):
        sliders.append(
            (ch, pygame.Rect(slider_x, slider_y + i * (sh + 4), slider_w, sh))
        )
    return {
        "swatches": swatches,
        "sv": sv,
        "hue": hue,
        "sliders": sliders,
    }


def _ensure_sv_surface(colors: ColorUniforms, pygame: Any, size: int, hue: float) -> Any:
    key = round(hue * 64.0)
    if colors._sv_surf is not None and colors._sv_cache_key == key:
        if colors._sv_surf.get_size() == (size, size):
            return colors._sv_surf
    # S horizontal, V vertical (top = high V) — classic painter square.
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    for yi in range(size):
        v = 1.0 - (yi / max(1, size - 1))
        for xi in range(size):
            s = xi / max(1, size - 1)
            arr[yi, xi] = _hsv_to_rgb8(hue, s, v)
    surf = pygame.surfarray.make_surface(np.transpose(arr, (1, 0, 2)))
    colors._sv_surf = surf
    colors._sv_cache_key = float(key)
    return surf


def _ensure_hue_surface(colors: ColorUniforms, pygame: Any, w: int, h: int) -> Any:
    if colors._hue_surf is not None and colors._hue_surf.get_size() == (w, h):
        return colors._hue_surf
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for yi in range(h):
        hue = yi / max(1, h - 1)
        arr[yi, :] = _hsv_to_rgb8(hue, 1.0, 1.0)
    surf = pygame.surfarray.make_surface(np.transpose(arr, (1, 0, 2)))
    colors._hue_surf = surf
    return surf


def _draw_color_panel(
    target: Any,
    pygame: Any,
    font: Any,
    rect: Any,
    colors: ColorUniforms,
) -> dict[str, Any]:
    """Draw Color strip; return hit-test layout dict."""
    if rect.width <= 0 or rect.height <= 0 or not colors.active:
        return _color_panel_layout(rect, colors, pygame)
    pygame.draw.rect(target, _COLOR_BG, rect)
    rgba = colors.current_rgba()
    hue_v, sat_v, val_v = _rgb_to_hsv(rgba[0], rgba[1], rgba[2])
    name = colors.current_name() or "?"

    title = font.render(f"Color  {name}", True, _COLOR_LABEL)
    label_w = max(100, title.get_width() + 16)
    hits = _color_panel_layout(rect, colors, pygame, label_w=label_w)
    target.blit(title, (rect.x + 8, rect.y + 8 + max(0, (22 - title.get_height()) // 2)))

    for i, srect in hits["swatches"]:
        pname, _ = colors.params[i]
        pr = colors.values.get(pname) or _default_color_rgba(pname)
        fill = (int(pr[0] * 255), int(pr[1] * 255), int(pr[2] * 255))
        pygame.draw.rect(target, fill, srect)
        rim = _LESSON_TITLE if i == colors.focus else _BEVEL_DARK
        pygame.draw.rect(target, rim, srect, 2 if i == colors.focus else 1)

    sv = hits["sv"]
    if sv.width > 0:
        sv_surf = _ensure_sv_surface(colors, pygame, sv.width, hue_v)
        if sv_surf.get_size() != (sv.width, sv.height):
            sv_surf = pygame.transform.smoothscale(sv_surf, (sv.width, sv.height))
        target.blit(sv_surf, sv.topleft)
        pygame.draw.rect(target, _BEVEL_LIGHT, sv, 1)
        cx = int(sv.x + sat_v * (sv.width - 1))
        cy = int(sv.y + (1.0 - val_v) * (sv.height - 1))
        pygame.draw.circle(target, (255, 255, 255), (cx, cy), 5, 1)
        pygame.draw.circle(target, (20, 20, 24), (cx, cy), 4, 1)

    hue_r = hits["hue"]
    if hue_r.width > 0:
        hue_surf = _ensure_hue_surface(colors, pygame, hue_r.width, hue_r.height)
        target.blit(hue_surf, hue_r.topleft)
        pygame.draw.rect(target, _BEVEL_LIGHT, hue_r, 1)
        hy = int(hue_r.y + hue_v * (hue_r.height - 1))
        pygame.draw.line(
            target, (255, 255, 255), (hue_r.x - 1, hy), (hue_r.right, hy), 2
        )

    labels = {"r": "R", "g": "G", "b": "B", "a": "A"}
    ch_idx = {"r": 0, "g": 1, "b": 2, "a": 3}
    for ch, srect in hits["sliders"]:
        pygame.draw.rect(target, _COLOR_SLIDER_TRACK, srect)
        val = rgba[ch_idx[ch]]
        fill_w = max(1, int(srect.width * val))
        fill_col = {
            "r": (180, 70, 70),
            "g": (70, 150, 80),
            "b": (70, 110, 190),
            "a": _COLOR_SLIDER_FILL,
        }[ch]
        pygame.draw.rect(
            target, fill_col, pygame.Rect(srect.x, srect.y, fill_w, srect.height)
        )
        pygame.draw.rect(target, _BEVEL_DARK, srect, 1)
        tag = font.render(labels[ch], True, _COLOR_MUTED)
        target.blit(tag, (srect.x - 12, srect.y - 1))

    hex_s = f"#{int(rgba[0]*255):02X}{int(rgba[1]*255):02X}{int(rgba[2]*255):02X}"
    readout = font.render(
        f"{hex_s}  {rgba[0]:.2f} {rgba[1]:.2f} {rgba[2]:.2f}",
        True,
        _COLOR_MUTED,
    )
    ry = rect.bottom - readout.get_height() - 6
    if ry > rect.y + 30:
        target.blit(readout, (rect.x + 8, ry))
    return hits


def _color_panel_hit(
    pos: tuple[int, int],
    hits: dict[str, Any],
) -> str | None:
    """Return drag/control id under ``pos``, or None."""
    for i, srect in hits.get("swatches", []):
        if srect.collidepoint(pos):
            return f"swatch:{i}"
    sv = hits.get("sv")
    if sv is not None and sv.width and sv.collidepoint(pos):
        return "sv"
    hue = hits.get("hue")
    if hue is not None and hue.width and hue.collidepoint(pos):
        return "hue"
    for ch, srect in hits.get("sliders", []):
        if srect.collidepoint(pos):
            return ch
    return None


def _color_panel_apply_drag(
    colors: ColorUniforms,
    hits: dict[str, Any],
    pos: tuple[int, int],
    control: str,
) -> bool:
    """Update focused color from pointer; return True if value changed."""
    rgba = colors.current_rgba()
    h, s, v = _rgb_to_hsv(rgba[0], rgba[1], rgba[2])
    before = tuple(rgba)

    if control == "sv":
        sv = hits["sv"]
        if sv.width <= 0:
            return False
        sx = min(1.0, max(0.0, (pos[0] - sv.x) / max(1, sv.width - 1)))
        vy = min(1.0, max(0.0, 1.0 - (pos[1] - sv.y) / max(1, sv.height - 1)))
        r, g, b = _hsv_to_rgb(h, sx, vy)
        colors.set_rgb(r, g, b)
    elif control == "hue":
        hue_r = hits["hue"]
        if hue_r.height <= 0:
            return False
        nh = min(1.0, max(0.0, (pos[1] - hue_r.y) / max(1, hue_r.height - 1)))
        r, g, b = _hsv_to_rgb(nh, s, v)
        colors.set_rgb(r, g, b)
    elif control in ("r", "g", "b", "a"):
        sliders = {ch: r for ch, r in hits["sliders"]}
        srect = sliders.get(control)
        if srect is None or srect.width <= 0:
            return False
        t = min(1.0, max(0.0, (pos[0] - srect.x) / max(1, srect.width - 1)))
        idx = {"r": 0, "g": 1, "b": 2, "a": 3}[control]
        colors.set_channel(idx, t)
    else:
        return False
    return tuple(colors.current_rgba()) != before


def _letterbox_rect(
    area: Any,
    src_w: int,
    src_h: int,
    pygame: Any,
) -> Any:
    """Fit ``src_w×src_h`` into ``area`` preserving aspect (letterbox / pillarbox)."""
    if area.width <= 0 or area.height <= 0 or src_w <= 0 or src_h <= 0:
        return pygame.Rect(area.x, area.y, max(1, area.width), max(1, area.height))
    scale = min(area.width / src_w, area.height / src_h)
    fw = max(1, int(round(src_w * scale)))
    fh = max(1, int(round(src_h * scale)))
    return pygame.Rect(
        area.x + (area.width - fw) // 2,
        area.y + (area.height - fh) // 2,
        fw,
        fh,
    )


def _cursor_screen_pos() -> tuple[int, int] | None:
    """Global cursor position (Win32); None if unavailable."""
    if not is_windows():
        return None
    try:
        import ctypes
        from ctypes import wintypes

        pt = wintypes.POINT()
        if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
            return int(pt.x), int(pt.y)
    except Exception:  # noqa: BLE001
        return None
    return None


def _draw_console(
    target: Any,
    pygame: Any,
    font: Any,
    lines: list[str],
    rect: Any,
    scroll_y: int,
) -> None:
    """Classic terminal: green mono text on near-black."""
    if rect.width <= 0 or rect.height <= 0:
        return
    pygame.draw.rect(target, _CONSOLE_BG, rect)
    pygame.draw.line(
        target,
        (40, 50, 45),
        (rect.left, rect.top),
        (rect.right, rect.top),
        1,
    )
    clip = target.get_clip()
    target.set_clip(rect)
    line_h = _console_line_height(font)
    glyph_h = font.get_height()
    glyph_oy = max(0, (line_h - glyph_h) // 2)
    y = rect.y + _PANEL_PAD - scroll_y
    text_w = max(40, rect.width - 2 * _PANEL_PAD)

    for raw in lines:
        # Soft-wrap long console lines.
        wrapped = _wrap_console_line(raw, font, text_w)
        for piece in wrapped:
            if y + line_h < rect.y:
                y += line_h
                continue
            if y > rect.bottom:
                target.set_clip(clip)
                return
            surf = font.render(piece, True, _CONSOLE_COLOR)
            target.blit(surf, (rect.x + _PANEL_PAD, y + glyph_oy))
            y += line_h
    target.set_clip(clip)


def _wrap_console_line(text: str, font: Any, max_width: int) -> list[str]:
    if not text:
        return [""]
    if font.size(text)[0] <= max_width:
        return [text]
    out: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                out.append(current)
            current = ch
    if current:
        out.append(current)
    return out or [""]


def _console_line_count(lines: list[str], font: Any, max_width: int) -> int:
    return sum(len(_wrap_console_line(line, font, max_width)) for line in lines)


def _catmull_rom_weights(t: float) -> tuple[float, float, float, float]:
    """Catmull-Rom basis for local parameter ``t`` in [0, 1] between knots p1→p2."""
    t2 = t * t
    t3 = t2 * t
    w0 = 0.5 * (-t3 + 2.0 * t2 - t)
    w1 = 0.5 * (3.0 * t3 - 5.0 * t2 + 2.0)
    w2 = 0.5 * (-3.0 * t3 + 4.0 * t2 + t)
    w3 = 0.5 * (t3 - t2)
    return w0, w1, w2, w3


def _catmull_rom_basis(n_out: int, n_in: int) -> np.ndarray:
    """Rows of 1D Catmull-Rom weights: ``(n_out, n_in)`` so ``B @ values`` upsamples.

    Edge knots are repeated (clamp) so the curve still hits the mesh endpoints.
    Separable ``By @ mesh @ Bx.T`` yields a smooth bicubic-style displacement field.
    """
    b = np.zeros((n_out, n_in), dtype=np.float64)
    if n_in <= 0:
        return b
    if n_in == 1:
        b[:, 0] = 1.0
        return b
    if n_in == 2:
        # Degenerate: fall back to linear between the two knots.
        t = np.linspace(0.0, 1.0, n_out, dtype=np.float64)
        b[:, 0] = 1.0 - t
        b[:, 1] = t
        return b

    t_all = np.linspace(0.0, n_in - 1, n_out, dtype=np.float64)
    for j, t in enumerate(t_all):
        i1 = int(math.floor(t))
        if i1 >= n_in - 1:
            i1 = n_in - 2
            f = 1.0
        else:
            f = float(t - i1)
        i0 = i1 - 1
        i2 = i1 + 1
        i3 = i1 + 2
        w0, w1, w2, w3 = _catmull_rom_weights(f)
        # Clamp knot indices (repeat edge samples).
        b[j, max(i0, 0)] += w0
        b[j, i1] += w1
        b[j, min(i2, n_in - 1)] += w2
        b[j, min(i3, n_in - 1)] += w3
    return b


class WobbleMesh:
    """2D jelly mesh: spring-damper + 4-neighbor coupling, Catmull-Rom remap.

    Control points are a dense ``rows × cols`` grid of horizontal displacements.
    The field is upsampled with **separable Catmull-Rom** (smooth sides; hits
    knots). Live compose warps the **full content frame** at full resolution
    (nearest) so shader + code + console wobble as one jelly; settled frames
    identity-blit. Left/right edge columns of the same displacement field drive
    ``CreatePolygonRgn`` so the HWND silhouette wraps the warped pixels.
    """

    def __init__(
        self, cols: int = _WOBBLE_COLS, rows: int = _WOBBLE_ROWS
    ) -> None:
        self.cols = max(2, int(cols))
        self.rows = max(2, int(rows))
        self.x = np.zeros((self.rows, self.cols), dtype=np.float64)
        self.v = np.zeros((self.rows, self.cols), dtype=np.float64)
        self.enabled = True
        self._last_win_pos: tuple[int, int] | None = None
        self._dragging_window = False
        # Cached Catmull-Rom bases / warp buffers (content size).
        self._basis_cache: dict[tuple[int, ...], tuple[np.ndarray, np.ndarray]] = {}
        self._warp_buf: np.ndarray | None = None
        self._map_buf: np.ndarray | None = None
        self._xc_cache: np.ndarray | None = None
        self._xc_cache_len: int = -1
        # Displacement fields keyed by (w, h); keep a small LRU.
        self._disp_caches: dict[tuple[int, int], np.ndarray] = {}
        self._profiled = False
        self._max_abs_x = 0.0
        self._max_abs_v = 0.0

    def _invalidate_disp_cache(self) -> None:
        self._disp_caches.clear()

    def _refresh_energy(self) -> None:
        self._max_abs_x = float(np.max(np.abs(self.x))) if self.x.size else 0.0
        self._max_abs_v = float(np.max(np.abs(self.v))) if self.v.size else 0.0

    def impulse(self, strength: float = 1.0, *, bias: float = 0.0) -> None:
        if not self.enabled:
            return
        self._invalidate_disp_cache()
        py = np.linspace(0.0, math.pi * 2.0, self.rows, endpoint=False)[:, None]
        px = np.linspace(0.0, math.pi, self.cols)[None, :]
        wave = np.sin(py * 1.5 + bias) + 0.35 * np.sin(py * 3.0 + bias * 0.7)
        # Slight X variation so left/right edges aren't locked together.
        wave = wave * (0.82 + 0.18 * np.cos(px + bias * 0.4))
        noise = np.random.uniform(-0.5, 0.5, size=self.x.shape)
        self.v += (wave + noise) * (90.0 * strength)
        self._refresh_energy()

    def poke_from_dx(self, dx: float, *, strong: bool = False) -> None:
        """Inject horizontal energy; strong=True for OS window title-bar drag."""
        if not self.enabled or abs(dx) < 0.5:
            return
        self._invalidate_disp_cache()
        # Lagging wave: top leads, bottom trails (classic Compiz jelly).
        phase_y = np.linspace(0.0, math.pi, self.rows)[:, None]
        lag_y = np.linspace(0.15, 1.0, self.rows)[:, None]
        phase_x = np.linspace(0.0, math.pi, self.cols)[None, :]
        gain = _WOBBLE_DRAG_GAIN if strong else 2.0
        disp = _WOBBLE_DRAG_DISP if strong else 0.09
        shape = np.sin(phase_y) * lag_y * (0.88 + 0.12 * np.cos(phase_x))
        self.v += shape * (-dx * gain)
        self.x += shape * (-dx * disp)
        np.clip(self.x, -_WOBBLE_MAX_PX, _WOBBLE_MAX_PX, out=self.x)
        self._refresh_energy()

    def poke_from_window_delta(self, dx: float, dy: float) -> None:
        """Title-bar / OS window move: strong full-frame jello energy."""
        if not self.enabled:
            return
        energy = abs(dx) + 0.35 * abs(dy)
        if energy < _WOBBLE_POS_EPS:
            return
        self._dragging_window = True
        self.poke_from_dx(float(dx), strong=True)
        if abs(dy) >= _WOBBLE_POS_EPS:
            self._invalidate_disp_cache()
            phase_y = np.linspace(0.0, math.pi * 2.0, self.rows, endpoint=False)[:, None]
            lag_y = np.linspace(0.2, 1.0, self.rows)[:, None]
            phase_x = np.linspace(0.0, math.pi, self.cols)[None, :]
            kick = np.sin(phase_y * 1.25) * lag_y * (0.85 + 0.15 * np.cos(phase_x))
            self.v += kick * (-dy * (_WOBBLE_DRAG_GAIN * 0.55))
            self.x += kick * (-dy * (_WOBBLE_DRAG_DISP * 0.35))
            np.clip(self.x, -_WOBBLE_MAX_PX, _WOBBLE_MAX_PX, out=self.x)
            self._refresh_energy()

    def update(self, dt: float) -> None:
        if not self.enabled:
            if self._max_abs_x != 0.0 or self._max_abs_v != 0.0:
                self.x.fill(0.0)
                self.v.fill(0.0)
                self._max_abs_x = 0.0
                self._max_abs_v = 0.0
                self._invalidate_disp_cache()
            self._dragging_window = False
            return
        # Already at rest: skip spring + cache churn (identity blit path).
        if self.nearly_still() and not self._dragging_window:
            if self._max_abs_x != 0.0 or self._max_abs_v != 0.0:
                self.x.fill(0.0)
                self.v.fill(0.0)
                self._max_abs_x = 0.0
                self._max_abs_v = 0.0
                self._invalidate_disp_cache()
            return
        dt = min(dt, 1.0 / 30.0)
        self._invalidate_disp_cache()
        # 4-neighbor coupling on the control grid.
        couple = np.zeros_like(self.x)
        couple[:, 1:] += self.x[:, :-1] - self.x[:, 1:]
        couple[:, :-1] += self.x[:, 1:] - self.x[:, :-1]
        couple[1:, :] += self.x[:-1, :] - self.x[1:, :]
        couple[:-1, :] += self.x[1:, :] - self.x[:-1, :]
        # Continuum-scale stiffness vs reference grid density.
        couple_k = _WOBBLE_COUPLE * ((self.rows / float(_WOBBLE_REF_ROWS)) ** 2)
        spring = _WOBBLE_SPRING * (0.55 if self._dragging_window else 1.0)
        damp = _WOBBLE_DAMP * (0.7 if self._dragging_window else 1.0)
        acc = -spring * self.x - damp * self.v + couple_k * couple
        self.v += acc * dt
        self.x += self.v * dt
        np.clip(self.x, -_WOBBLE_MAX_PX, _WOBBLE_MAX_PX, out=self.x)
        self._refresh_energy()
        if self.nearly_still():
            self._dragging_window = False
            self.x.fill(0.0)
            self.v.fill(0.0)
            self._max_abs_x = 0.0
            self._max_abs_v = 0.0

    def nearly_still(self) -> bool:
        return self._max_abs_x < _WOBBLE_STILL_X and self._max_abs_v < _WOBBLE_STILL_V

    def _ensure_remap_cache(self, w: int, h: int) -> tuple[np.ndarray, np.ndarray]:
        key = (w, h, self.rows, self.cols)
        hit = self._basis_cache.get(key)
        if hit is not None:
            return hit
        bx = _catmull_rom_basis(w, self.cols)
        by = _catmull_rom_basis(h, self.rows)
        if len(self._basis_cache) >= 2:
            self._basis_cache.pop(next(iter(self._basis_cache)))
        self._basis_cache[key] = (bx, by)
        return bx, by

    def displacement_field(self, w: int, h: int) -> np.ndarray:
        """Catmull-Rom upsample mesh ``x`` to a (w, h) horizontal displacement field."""
        key = (int(w), int(h))
        cached = self._disp_caches.get(key)
        if cached is not None:
            return cached
        bx, by = self._ensure_remap_cache(w, h)
        # ``by @ x @ bx.T`` → (h, w); transpose to pygame (w, h).
        field = (by @ self.x @ bx.T).T
        if len(self._disp_caches) >= 2:
            self._disp_caches.pop(next(iter(self._disp_caches)))
        self._disp_caches[key] = field
        return field

    def _warp_remap(
        self,
        pygame: Any,
        src: Any,
        dest: Any,
        *,
        origin_x: int,
        fill_color: tuple[int, int, int],
        scale_disp: float,
        profile: bool,
    ) -> float | None:
        """Horizontal nearest remap of ``src`` into ``dest`` (same pixel size)."""
        w, h = src.get_size()
        dw = int(dest.get_width())
        dh = int(dest.get_height())
        if dh != h:
            raise ValueError("warp src/dest height mismatch")

        t0 = time.perf_counter() if profile else None
        # Mesh units are full-content pixels (always full-res remap).
        disp = self.displacement_field(w, h)
        if scale_disp != 1.0:
            disp = disp * scale_disp

        ox = max(0, min(int(origin_x), dw))
        if (
            self._map_buf is None
            or self._map_buf.shape != (dw, h)
            or self._warp_buf is None
            or self._warp_buf.shape != (dw, h, 3)
        ):
            self._map_buf = np.empty((dw, h), dtype=np.float64)
            self._warp_buf = np.empty((dw, h, 3), dtype=np.uint8)
        map_x = self._map_buf
        if ox > 0:
            map_x[:ox, :] = disp[0:1, :]
        end = min(dw, ox + w)
        if end > ox:
            map_x[ox:end, :] = disp[: end - ox, :]
        if end < dw:
            map_x[end:, :] = disp[-1:, :]
        if self._xc_cache is None or self._xc_cache_len != dw:
            self._xc_cache = np.arange(dw, dtype=np.float64)[:, None]
            self._xc_cache_len = dw
        # map_x := (column - origin_x) - disp
        np.subtract(self._xc_cache, map_x, out=map_x)
        map_x -= float(origin_x)

        src_rgb = np.asarray(pygame.surfarray.array3d(src))
        assert self._warp_buf is not None
        if _HAS_NUMBA:
            if t0 is not None and not self._profiled:
                # Warm compile, then time the steady-state call.
                _warp_horizontal_nearest_numba(
                    src_rgb,
                    map_x,
                    self._warp_buf,
                    int(fill_color[0]),
                    int(fill_color[1]),
                    int(fill_color[2]),
                )
                t0 = time.perf_counter()
            _warp_horizontal_nearest_numba(
                src_rgb,
                map_x,
                self._warp_buf,
                int(fill_color[0]),
                int(fill_color[1]),
                int(fill_color[2]),
            )
            warped = self._warp_buf
        else:
            warped = _warp_horizontal_nearest_numpy(src_rgb, map_x, fill=fill_color)

        pygame.surfarray.blit_array(dest, warped)
        if t0 is None:
            return None
        return (time.perf_counter() - t0) * 1000.0

    def blit(
        self,
        pygame: Any,
        dest: Any,
        src: Any,
        *,
        origin_x: int = 0,
        fill_color: tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        """Remap full ``src`` onto ``dest`` via horizontal mesh displacement.

        Always full-resolution nearest sampling (no half-res / smoothscale).
        When settled, identity-blits. Destination column ``X`` samples source at
        ``(X - origin_x) - disp`` — same field as ``edge_curves``.
        """
        w, h = src.get_size()
        dw = int(dest.get_width())
        dest.fill(fill_color)
        if not self.enabled or self.nearly_still():
            dest.blit(src, (origin_x, 0))
            return

        profile = _WOBBLE_PROFILE_ONCE and not self._profiled
        ms = self._warp_remap(
            pygame,
            src,
            dest,
            origin_x=origin_x,
            fill_color=fill_color,
            scale_disp=1.0,
            profile=profile,
        )
        if ms is not None:
            self._profiled = True
            backend = "numba" if _HAS_NUMBA else "numpy"
            print(
                f"[wobble] mesh {self.cols}x{self.rows} Catmull-Rom + full-res "
                f"remap {dw}x{h} ({backend}): {ms:.2f} ms/frame"
            )

    def edge_curves(
        self, content_w: int, content_h: int, *, step: int = _WOBBLE_OUTLINE_STEP
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Per-row left/right offsets from the **same** Catmull-Rom field as ``blit``.

        Default ``step`` trades silhouette density vs ``CreatePolygonRgn`` cost.
        Returns ``(ys, left_ox, right_ox)`` relative to the settled content rect.
        """
        if not self.enabled or self.nearly_still() or content_h <= 0 or content_w <= 0:
            ys = np.array([0, max(0, content_h - 1)], dtype=np.int32)
            z = np.zeros(2, dtype=np.float64)
            return ys, z, z

        step = max(1, int(step))
        ys_list = list(range(0, content_h, step))
        last = content_h - 1
        if not ys_list or ys_list[-1] != last:
            ys_list.append(last)
        ys = np.asarray(ys_list, dtype=np.int32)
        disp = self.displacement_field(content_w, content_h)
        left = disp[0, ys]
        right = disp[content_w - 1, ys]
        return ys, left, right

    def strip_offsets(self) -> np.ndarray:
        """Legacy: mean row offsets (prefer ``edge_curves`` for silhouettes)."""
        if not self.enabled or self.nearly_still():
            return np.zeros(self.rows, dtype=np.float64)
        return np.mean(self.x, axis=1)


def _window_pos(pygame: Any) -> tuple[int, int] | None:
    """Best-effort top-left of the window for title-bar drag-wobble impulses."""
    # pygame 2.0.2+ exposes SDL window position directly.
    getter = getattr(pygame.display, "get_window_position", None)
    if callable(getter):
        try:
            pos = getter()
            if pos is not None and len(pos) >= 2:
                return int(pos[0]), int(pos[1])
        except Exception:  # noqa: BLE001
            pass
    try:
        info = pygame.display.get_wm_info()
        hwnd = info.get("window")
        if hwnd is None:
            return None
        import ctypes
        from ctypes import wintypes

        rect = wintypes.RECT()
        if ctypes.windll.user32.GetWindowRect(int(hwnd), ctypes.byref(rect)):
            return int(rect.left), int(rect.top)
    except Exception:  # noqa: BLE001
        return None
    return None


def _file_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return -1.0


def run_live(
    shader: Path,
    entry: str,
    width: int,
    height: int,
    poll_s: float = 0.15,
    *,
    lessons: list[Lesson] | None = None,
    lesson_index: int | None = None,
    school_tabs: list[tuple[str, Path]] | None = None,
    school_3d: bool = False,
) -> int:
    """Open a pygame window with in-window editor + temp hotswap recompile."""
    try:
        import pygame
    except ImportError as exc:
        raise SystemExit(
            "pygame is required for live preview. Install with: pip install pygame"
        ) from exc

    shader = _resolve_shader(shader)
    if not shader.exists():
        raise SystemExit(f"shader not found: {shader}")

    school_bufs: list[dict[str, Any]] = []
    school_i = 0
    preview_i = 0
    if school_tabs:
        for lab, pth in school_tabs:
            rp = _resolve_shader(pth)
            if not rp.exists():
                raise SystemExit(f"school tab shader not found: {rp}")
            text = _read_shader_source(rp)
            school_bufs.append(
                {"label": lab, "path": rp, "text": text, "disk": text}
            )
        preview_i = 0
        for i, buf in enumerate(school_bufs):
            if "hello_pixel" in buf["text"] or buf["path"].name.endswith("_diff.slang"):
                preview_i = i
        shader = school_bufs[preview_i]["path"]
        school_i = 0

    curriculum = lessons if lessons is not None else load_curriculum()
    if school_3d:
        curriculum = []
        lesson_index = None
    cur_lesson_i = lesson_index
    if cur_lesson_i is None and curriculum:
        # Best-effort: match starting shader to a curriculum entry.
        resolved = shader.resolve()
        for les in curriculum:
            if les.shader.resolve() == resolved:
                cur_lesson_i = les.index
                break

    hotswap = hotswap_temp_path(shader)
    hotswap.parent.mkdir(parents=True, exist_ok=True)

    lesson_label = ""
    if cur_lesson_i is not None and curriculum:
        les0 = curriculum[cur_lesson_i]
        lesson_label = f"lesson {les0.index} {les0.id} — {les0.title}"

    print(f"VERNACULAR    shader={shader}")
    print(f"              hotswap={hotswap}")
    print(f"              entry={entry}  size={width}x{height}")
    if lesson_label:
        print(f"              {lesson_label}")
    print("Edit in the side panel — temp hotswap recompiles (Save writes the real file).")
    print(
        "Note: prefer F11 window FS; F10/cyan shader-only FS can black out the display "
        "(pinned — fix later)."
    )
    # Windows: borderless + shaped HWND so the *window outline* follows the jelly mesh.
    shaped_windows = is_windows()
    nav_hint = (
        " · [/] or <-/-> lesson · Ctrl+[/] always · L list · < > buttons" if curriculum else ""
    )
    editor_keys = (
        "Ctrl+Z undo · Ctrl+Y / Ctrl+Shift+Z redo · Ctrl+C/X/V clipboard · "
        "drag / Shift+arrows select"
    )
    move_hint = (
        "title bar / Alt+drag / middle-drag moves window · "
        "interactive lessons: drag shader to look"
    )
    if shaped_windows:
        print(
            "Keys: Esc exit FS / quit · Ctrl+S save · Ctrl+Enter recompile · "
            "F11 window FS · F10 / Shift+F11 shader FS · "
            f"{editor_keys} · W wobble (when editor unfocused){nav_hint} · "
            f"{move_hint} · window is resizable"
        )
    else:
        print(
            "Keys: Esc exit FS / quit · Ctrl+S save · Ctrl+Enter recompile · "
            "F11 window FS · F10 / Shift+F11 shader FS · "
            f"{editor_keys} · W wobble (when editor unfocused){nav_hint} · "
            f"{move_hint} · wobble hidden in FS · window is resizable"
        )
        print(
            "(Shaped Compiz outline is Windows-first; this platform keeps a rectangular window.)"
        )

    get_device()
    module: Any | None = None
    last_ok: np.ndarray = np.zeros((height, width, 3), dtype=np.float32)
    status = "loading…"
    last_error = ""
    fs_mode: str | None = None  # None | _FS_WINDOW | _FS_SHADER
    t0 = time.perf_counter()
    entry_has_time = False
    entry_has_mouse = False
    color_uniforms = ColorUniforms()
    lesson_textures = LessonTextures()
    if cur_lesson_i is not None and curriculum:
        les_tex = curriculum[cur_lesson_i].texture
        if les_tex is not None:
            lesson_textures.set_path(les_tex)
    color_hits: dict[str, Any] = {
        "swatches": [],
        "sv": None,
        "hue": None,
        "sliders": [],
    }
    interactive_mouse = False
    if cur_lesson_i is not None and curriculum:
        interactive_mouse = bool(curriculum[cur_lesson_i].interactive_mouse)
    # ShaderToy-style mouse: pixel coords in shader space (top-left). (0,0)=unset default.
    mouse_xy = (0.0, 0.0)
    mouse_dxy = (0.0, 0.0)
    mouse_btn = 0
    shader_frame_dirty = True
    frame_surf: Any = None
    canvas_surf: Any = None
    code_cache_surf: Any = None
    code_cache_key: tuple[Any, ...] | None = None
    editor = CodeEditor()
    if school_bufs:
        editor.set_text(school_bufs[school_i]["text"], dirty=False)
    else:
        editor.set_text(_read_shader_source(shader), dirty=False)
    # Start unfocused so [ ] / arrows bank through examples immediately.
    editor.focused = False
    lesson_lines: list[str] = []
    if cur_lesson_i is not None and curriculum:
        lesson_lines = lesson_banner_lines(curriculum[cur_lesson_i])
    console_lines: list[str] = [
        f"[VERNACULAR] {shader.name}::{entry}"
        + (f"  ({lesson_label})" if lesson_label else ""),
        f"[live] edit in-window -> temp hotswap; Save writes {shader.name}",
        "[live] entries with float time get seconds-since-start each frame",
        "[live] mouse: float2 mouse / mouse_delta / int mouse_down when declared",
        "[live] color: float3/float4 color|albedo|tint|… get Color panel (swatch / HSV / RGB)",
        "[live] color: hover float3 / color param in editor to focus that picker",
        "[live] texture: Texture2D+SamplerState from curriculum texture (numpy fallback)",
        "[live] window move: title bar · Alt+drag shader · middle-button drag",
        "[live] chrome: frosted title · traffic (red close · green window-FS · cyan shader-FS)",
        "[live] FS: prefer F11 / green window FS · F10/cyan shader-only can black out (pinned)",
        "[live] AA: ShaderToy ports (ocean/circle) use 3x3 supersample + light present sharpen",
        "[live] Ctrl+Z/Y undo/redo · select + Ctrl+C/X/V · resize window to reflow",
    ]
    if school_3d:
        console_lines.append(
            "[school] VS / PS / Diff tabs — Save writes the active file for Falcor F5"
        )
        console_lines.append(
            "[school] preview is Diff (hello_pixel). VS/PS edit 3D Temple, not this 2D view."
        )
        console_lines.append(
            "[school] Diff = [Differentiable] lab twin; 3D raster does not run bwd_diff this pass."
        )
    if curriculum:
        console_lines.append(
            "[live] curriculum: [ / Left prev · ] / Right next · Ctrl+[ / ] always · L list · 0-9 · < >"
        )
        for line in lesson_lines:
            console_lines.append(f"[lesson] {line}")
    if interactive_mouse:
        console_lines.append(
            "[live] interactive_mouse: drag shader to look · do not window-drag on primary"
        )
    console_scroll = 0
    console_follow = True
    wobble = WobbleMesh()
    need_reload = True
    edit_recompile_at: float | None = None
    real_mtime = _file_mtime(shader)
    pressed_btn: str | None = None

    school_tab_rects: list[tuple[int, Any]] = []

    def _preview_text() -> str:
        if not school_bufs:
            return editor.get_text()
        if school_i == preview_i:
            return editor.get_text()
        return str(school_bufs[preview_i]["text"])

    def write_hotswap() -> None:
        hotswap.write_text(_preview_text(), encoding="utf-8", newline="\n")

    def switch_school_tab(new_i: int) -> None:
        nonlocal school_i, real_mtime
        if not school_bufs or new_i == school_i:
            return
        school_bufs[school_i]["text"] = editor.get_text()
        school_i = new_i
        buf = school_bufs[school_i]
        editor.set_text(str(buf["text"]), dirty=False)
        editor._saved_text = str(buf["disk"])
        editor.dirty = str(buf["text"]) != str(buf["disk"])
        editor.scroll_y = 0
        editor.scroll_x = 0
        real_mtime = _file_mtime(buf["path"])
        caption()
        log(f"[school] tab {buf['label']} — {buf['path'].name}")
        if school_i != preview_i:
            log("[school] preview stays on Diff; Save this file then F5 in VernacularViewport")

    # Seed temp from editor before first compile.
    write_hotswap()

    pygame.init()
    try:
        pygame.scrap.init()
    except Exception:  # noqa: BLE001
        pass
    use_title_bar = shaped_windows
    content_w, content_h = _window_client_size(width, height, title_bar=use_title_bar)
    min_cw, min_ch = _min_window_client_size(title_bar=use_title_bar)
    pad_x = wobble_pad_x(_WOBBLE_MAX_PX) if shaped_windows else 0
    disp_w = content_w + 2 * pad_x
    disp_h = content_h
    shaped: Win32ShapedHost | None = None
    shaped_mode = "none"

    base_flags = pygame.RESIZABLE | (pygame.NOFRAME if shaped_windows else 0)
    screen = pygame.display.set_mode((disp_w, disp_h), base_flags)
    if shaped_windows:
        shaped = Win32ShapedHost(pad_x)
        info = shaped.attach(pygame)
        shaped_mode = info.mode
        if shaped_mode == "none":
            print(f"[shaped] unavailable — {info.detail}")
            print("[shaped] falling back to borderless rectangular window")
            pad_x = 0
            disp_w = content_w
            screen = pygame.display.set_mode((disp_w, disp_h), base_flags)
            shaped = None
        else:
            pad_x = info.pad_x
            print(f"[shaped] mode={shaped_mode} — {info.detail}")
            console_lines.append(f"[shaped] {shaped_mode}: window silhouette follows wobble mesh")
            if shaped_mode == "colorkey":
                console_lines.append(
                    "[shaped] color-key fallback: pads transparent; prefer SetWindowRgn"
                )
    clock = pygame.time.Clock()
    # SysFont + antialiased render; title uses 2x font for smoothscale-down AA.
    font = pygame.font.SysFont("consolas", _FONT_CONSOLE)
    code_font = pygame.font.SysFont("consolas", _FONT_CODE)
    btn_font = pygame.font.SysFont("consolas", _FONT_BTN)
    title_font = pygame.font.SysFont("consolas", _FONT_TITLE, bold=True)
    title_font_hi = pygame.font.SysFont(
        "consolas", _FONT_TITLE * _LABEL_AA_SCALE, bold=True
    )

    # Warm Numba warp so the first real wobble frame isn't a multi-second compile stall.
    if _HAS_NUMBA:
        try:
            _zw, _zh = 32, 24
            _warp_horizontal_nearest_numba(
                np.zeros((_zw, _zh, 3), dtype=np.uint8),
                np.zeros((_zw + 4, _zh), dtype=np.float64),
                np.empty((_zw + 4, _zh, 3), dtype=np.uint8),
                0,
                0,
                0,
            )
        except Exception:  # noqa: BLE001
            pass

    def lesson_title_bit() -> str:
        if cur_lesson_i is None or not curriculum:
            return ""
        les = curriculum[cur_lesson_i]
        return f"{les.index}:{les.title} — "

    def caption() -> None:
        star = "*" if editor.dirty else ""
        if school_3d:
            pygame.display.set_caption("VERNACULAR — 3D school VS/PS/Diff")
            return
        pygame.display.set_caption(
            f"VERNACULAR — {lesson_title_bit()}{shader.name}{star}::{entry}"
        )

    caption()

    def content_origin() -> tuple[int, int]:
        """Top-left of the composited UI inside the (possibly padded) HWND."""
        if fs_mode is not None or not shaped_windows:
            return 0, 0
        return pad_x, 0

    def layout() -> tuple[Any, ...]:
        """Return title, img, btn_bar, code, lesson, color, console, content,
        save, reload, prev, next, close, amber, green, cyan rects.

        Two squares when possible: shader | code (code width tracks letterbox
        height / display side). Lesson strip + Color panel + console span width.
        Window FS keeps chrome; shader FS is image-only.
        """
        ox, oy = content_origin()
        empty = pygame.Rect(0, 0, 0, 0)
        if fs_mode == _FS_SHADER:
            sw, sh = screen.get_size()
            return (
                empty,
                pygame.Rect(0, 0, sw, sh),
                empty,
                empty,
                empty,
                empty,
                empty,
                pygame.Rect(0, 0, sw, sh),
                empty,
                empty,
                empty,
                empty,
                empty,
                empty,
                empty,
                empty,
            )

        if fs_mode == _FS_WINDOW:
            lay_w, lay_h = screen.get_size()
        else:
            lay_w, lay_h = content_w, content_h

        title_h = _TITLE_BAR_H if use_title_bar else 0
        title_rect = (
            pygame.Rect(ox, oy, lay_w, title_h) if title_h else empty
        )
        body_y = oy + title_h
        content = pygame.Rect(
            ox + _CHROME,
            body_y + _CHROME,
            lay_w - 2 * _CHROME,
            lay_h - title_h - 2 * _CHROME,
        )
        lesson_h = _LESSON_STRIP_H if curriculum else 0
        color_h = _COLOR_PANEL_H if color_uniforms.active else 0
        below = _CONSOLE_H
        if lesson_h:
            below += lesson_h + _DIVIDER
        if color_h:
            below += color_h + _DIVIDER
        top_h = max(1, content.height - _DIVIDER - below)
        avail_w = max(1, content.width - _DIVIDER)
        # Equal square side: limited by row height and half the available width.
        side = max(1, min(top_h, avail_w // 2))
        shader_area_w = side
        code_w = side
        pair_w = shader_area_w + _DIVIDER + code_w
        pair_x = content.x + max(0, (content.width - pair_w) // 2)

        shader_area = pygame.Rect(pair_x, content.y, shader_area_w, top_h)
        img_rect = _letterbox_rect(shader_area, width, height, pygame)

        # Code column tracks letterboxed shader height (matching square for --size N).
        track = max(1, img_rect.height)
        if track != code_w and track + _DIVIDER + max(img_rect.width, 1) <= content.width:
            code_w = track
            shader_area_w = max(1, img_rect.width)
            pair_w = shader_area_w + _DIVIDER + code_w
            pair_x = content.x + max(0, (content.width - pair_w) // 2)
            shader_area = pygame.Rect(pair_x, content.y, shader_area_w, top_h)
            img_rect = _letterbox_rect(shader_area, width, height, pygame)

        panel_x = pair_x + shader_area_w + _DIVIDER
        btn_bar = pygame.Rect(panel_x, content.y, code_w, _BTN_BAR_H)
        code_rect = pygame.Rect(
            panel_x,
            content.y + _BTN_BAR_H,
            code_w,
            max(1, top_h - _BTN_BAR_H),
        )
        lesson_y = content.y + top_h + _DIVIDER
        lesson_rect = (
            pygame.Rect(content.x, lesson_y, content.width, lesson_h)
            if lesson_h
            else empty
        )
        color_y = lesson_y + lesson_h + (_DIVIDER if lesson_h else 0)
        color_rect = (
            pygame.Rect(content.x, color_y, content.width, color_h)
            if color_h
            else empty
        )
        console_y = color_y + color_h + (_DIVIDER if color_h else 0)
        console_rect = pygame.Rect(
            content.x,
            console_y,
            content.width,
            _CONSOLE_H,
        )
        by = btn_bar.y + (_BTN_BAR_H - _BTN_H) // 2
        bx = btn_bar.x + _PANEL_PAD
        save_btn = pygame.Rect(bx, by, _BTN_W, _BTN_H)
        reload_btn = pygame.Rect(bx + _BTN_W + _BTN_GAP, by, _BTN_W + 8, _BTN_H)
        prev_btn = empty
        next_btn = empty
        school_tab_rects.clear()
        if curriculum:
            prev_btn = pygame.Rect(
                reload_btn.right + _BTN_GAP + 8, by, 36, _BTN_H
            )
            next_btn = pygame.Rect(prev_btn.right + _BTN_GAP, by, 36, _BTN_H)
        elif school_bufs:
            tx = reload_btn.right + _BTN_GAP + 8
            for i, buf in enumerate(school_bufs):
                tw = max(40, 10 * len(str(buf["label"])) + 16)
                r = pygame.Rect(tx, by, tw, _BTN_H)
                school_tab_rects.append((i, r))
                tx = r.right + 4
        close_btn = empty
        amber_btn = empty
        green_btn = empty
        cyan_btn = empty
        if title_h:
            cy = title_rect.y + title_h // 2
            x0 = title_rect.x + _TRAFFIC_PAD_X + _TRAFFIC_R
            hit = _TRAFFIC_R * 2 + 4
            step = _TRAFFIC_R * 2 + _TRAFFIC_GAP

            def _traffic_hit(i: int) -> Any:
                return pygame.Rect(
                    x0 + i * step - _TRAFFIC_R - 2,
                    cy - _TRAFFIC_R - 2,
                    hit,
                    hit,
                )

            close_btn = _traffic_hit(0)
            amber_btn = _traffic_hit(1)
            green_btn = _traffic_hit(2)
            cyan_btn = _traffic_hit(3)
        return (
            title_rect,
            img_rect,
            btn_bar,
            code_rect,
            lesson_rect,
            color_rect,
            console_rect,
            content,
            save_btn,
            reload_btn,
            prev_btn,
            next_btn,
            close_btn,
            amber_btn,
            green_btn,
            cyan_btn,
        )

    def apply_client_size(new_w: int, new_h: int, *, from_event: bool = False) -> None:
        """Clamp and apply a new content client size (excludes wobble pad)."""
        nonlocal content_w, content_h, disp_w, disp_h, screen, shaped, shaped_mode, pad_x
        content_w = max(min_cw, int(new_w))
        content_h = max(min_ch, int(new_h))
        if fs_mode is not None:
            return
        disp_w = content_w + 2 * pad_x
        disp_h = content_h
        if from_event:
            # SDL already resized; keep surface in sync if size drifted from clamp.
            cur = screen.get_size()
            if cur != (disp_w, disp_h):
                screen = pygame.display.set_mode((disp_w, disp_h), base_flags)
                if shaped_windows and shaped is not None:
                    shaped = Win32ShapedHost(pad_x)
                    info = shaped.attach(pygame)
                    shaped_mode = info.mode
                    if shaped_mode == "none":
                        shaped = None
                        pad_x = 0
                        disp_w = content_w
                        screen = pygame.display.set_mode((disp_w, disp_h), base_flags)
                    else:
                        pad_x = info.pad_x
            wobble._last_win_pos = None
            return
        screen = pygame.display.set_mode((disp_w, disp_h), base_flags)
        if shaped_windows:
            shaped = Win32ShapedHost(pad_x)
            info = shaped.attach(pygame)
            shaped_mode = info.mode
            if shaped_mode == "none":
                pad_x = 0
                disp_w = content_w
                screen = pygame.display.set_mode((disp_w, disp_h), base_flags)
                shaped = None
            else:
                pad_x = info.pad_x
        wobble._last_win_pos = None

    def set_fs_mode(mode: str | None) -> None:
        """Enter/leave fullscreen. mode: None | window | shader."""
        nonlocal screen, fs_mode, shaped, shaped_mode, pad_x, disp_w
        if mode not in (None, _FS_WINDOW, _FS_SHADER):
            mode = None
        prev = fs_mode
        fs_mode = mode
        if shaped is not None:
            shaped.clear_region()
        if fs_mode is not None:
            desk = _desktop_size(pygame)
            # Switching between window/shader FS: reuse FULLSCREEN surface when possible.
            if prev is None:
                screen = pygame.display.set_mode(desk, pygame.FULLSCREEN)
            elif screen.get_size() != desk:
                screen = pygame.display.set_mode(desk, pygame.FULLSCREEN)
            wobble._last_win_pos = None
            label = "window (IDE chrome)" if fs_mode == _FS_WINDOW else "shader-only"
            log(f"[fs] {label} — Esc to exit")
        else:
            pad_x = wobble_pad_x(_WOBBLE_MAX_PX) if shaped_windows else 0
            disp_w = content_w + 2 * pad_x
            screen = pygame.display.set_mode((disp_w, disp_h), base_flags)
            wobble._last_win_pos = None
            if shaped_windows:
                shaped = Win32ShapedHost(pad_x)
                info = shaped.attach(pygame)
                shaped_mode = info.mode
                if shaped_mode == "none":
                    pad_x = 0
                    disp_w = content_w
                    screen = pygame.display.set_mode((disp_w, disp_h), base_flags)
                    shaped = None
                    log(f"[shaped] re-attach failed — {info.detail}")
                else:
                    pad_x = info.pad_x
                    log(f"[shaped] re-attached mode={shaped_mode}")
            if prev is not None:
                log("[fs] windowed")

    def toggle_window_fs() -> None:
        set_fs_mode(None if fs_mode == _FS_WINDOW else _FS_WINDOW)

    def toggle_shader_fs() -> None:
        set_fs_mode(None if fs_mode == _FS_SHADER else _FS_SHADER)

    def log(msg: str, *, also_print: bool = True) -> None:
        nonlocal console_scroll, console_follow
        console_lines.append(msg)
        if len(console_lines) > _MAX_CONSOLE_LINES:
            del console_lines[: len(console_lines) - _MAX_CONSOLE_LINES]
        if also_print:
            print(msg)
        if console_follow:
            console_scroll = 10**9  # clamped later when drawing

    def schedule_edit_recompile() -> None:
        nonlocal edit_recompile_at
        if school_bufs and school_i != preview_i:
            caption()
            return
        edit_recompile_at = time.monotonic() + _EDIT_DEBOUNCE_S
        caption()

    def try_recompile(*, reason: str = "hotswap") -> None:
        nonlocal module, last_ok, status, last_error, need_reload, edit_recompile_at
        nonlocal entry_has_time, entry_has_mouse, shader_frame_dirty, frame_surf
        edit_recompile_at = None
        write_hotswap()
        module = None
        clear_module_cache()
        gc.collect()
        try:
            # Compile from temp; search real parent + slang/ for imports.
            module = load_module_from_path(
                hotswap,
                search_paths=[SLANG_DIR, shader.parent],
                fresh=True,
            )
            elapsed = time.perf_counter() - t0
            fn = getattr(module, entry)
            entry_has_time = _entry_accepts_time(fn)
            entry_has_mouse = _entry_accepts_mouse(fn)
            new_colors = color_uniforms.sync(fn)
            last_ok = render_frame(
                module,
                entry,
                width,
                height,
                time_s=elapsed,
                mouse=mouse_xy,
                mouse_delta=mouse_dxy,
                mouse_down=mouse_btn,
                colors=color_uniforms,
                textures=lesson_textures,
            )
            shader_frame_dirty = True
            frame_surf = None
            status = "ok"
            last_error = ""
            log(f"[reload] {reason} ok ({hotswap.name})")
            if entry_has_mouse:
                log("[mouse] entry accepts mouse uniforms")
            tex_n, samp_n = _entry_texture_bindings(fn)
            if tex_n or samp_n:
                tex_path = lesson_textures.path or _default_texture_path()
                log(f"[texture] {', '.join(tex_n + samp_n)} ← {tex_path.name}")
            if color_uniforms.active:
                names = ", ".join(n for n, _ in color_uniforms.params)
                log(f"[color] pickers: {names}")
                for n in new_colors:
                    log(f"[color] defaulted {n}")
            elif reason.startswith("lesson") or reason in ("start", "disk", "hotswap", "edit", "ctrl+enter"):
                # Quiet empty state — one tip so TAs know how to enable pickers.
                if reason in ("start",) or reason.startswith("lesson"):
                    log(
                        "[color] no color uniforms — add float3 color / albedo / tint …"
                    )
            wobble.impulse(0.85, bias=time.monotonic())
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
            status = "error"
            log(f"[reload] FAILED: {last_error}")
            traceback.print_exc()
            wobble.impulse(1.1, bias=1.7)
        finally:
            need_reload = False

    def do_save() -> None:
        nonlocal real_mtime
        try:
            target = school_bufs[school_i]["path"] if school_bufs else shader
            text = editor.get_text()
            target.write_text(text, encoding="utf-8", newline="\n")
            if school_bufs:
                school_bufs[school_i]["text"] = text
                school_bufs[school_i]["disk"] = text
            write_hotswap()
            editor.mark_saved()
            real_mtime = _file_mtime(target)
            caption()
            log(f"[save] wrote {target}")
        except OSError as exc:
            log(f"[save] FAILED: {exc}")

    def do_reload_from_disk(*, discard_dirty: bool = True) -> None:
        nonlocal real_mtime, edit_recompile_at
        was_dirty = editor.dirty
        src = school_bufs[school_i]["path"] if school_bufs else shader
        text = _read_shader_source(src)
        editor.set_text(text, dirty=False)
        if school_bufs:
            school_bufs[school_i]["text"] = text
            school_bufs[school_i]["disk"] = text
        editor.scroll_y = 0
        editor.scroll_x = 0
        real_mtime = _file_mtime(src)
        edit_recompile_at = None
        caption()
        if was_dirty and discard_dirty:
            log(f"[reload] discarded unsaved edits; re-read {shader.name}")
        else:
            log(f"[reload] re-read {shader.name} from disk")
        try_recompile(reason="disk")

    def switch_lesson(new_index: int) -> None:
        """Load curriculum lesson into editor + hotswap; update title."""
        nonlocal shader, entry, hotswap, real_mtime, edit_recompile_at, cur_lesson_i, t0
        nonlocal interactive_mouse, mouse_xy, mouse_dxy, mouse_btn, lesson_lines
        if not curriculum:
            log("[lesson] no curriculum loaded")
            return
        n = len(curriculum)
        new_index = int(new_index) % n
        if cur_lesson_i is not None and new_index == cur_lesson_i:
            return
        if editor.dirty:
            log("[lesson] discarding unsaved edits to switch lesson")
        les = curriculum[new_index]
        if not les.shader.exists():
            log(f"[lesson] FAILED: missing shader {les.shader}")
            return
        cur_lesson_i = new_index
        shader = les.shader
        entry = les.entry
        interactive_mouse = bool(les.interactive_mouse)
        mouse_xy = (0.0, 0.0)
        mouse_dxy = (0.0, 0.0)
        mouse_btn = 0
        color_uniforms.clear()
        if les.texture is not None:
            lesson_textures.set_path(les.texture)
        else:
            lesson_textures.clear()
        hotswap = hotswap_temp_path(shader)
        hotswap.parent.mkdir(parents=True, exist_ok=True)
        editor.set_text(_read_shader_source(shader), dirty=False)
        editor.scroll_y = 0
        editor.scroll_x = 0
        editor.focused = False
        real_mtime = _file_mtime(shader)
        edit_recompile_at = None
        t0 = time.perf_counter()  # reset time uniform for animated lessons
        lesson_lines = lesson_banner_lines(les)
        caption()
        log(f"[lesson] {les.index}/{n - 1}  {les.id} — {les.title}")
        for line in lesson_lines[1:]:
            log(f"[lesson] {line}")
        if interactive_mouse:
            log("[mouse] interactive: drag shader to look · title/Alt/middle moves window")
        try_recompile(reason=f"lesson {les.id}")

    def lesson_delta(delta: int) -> None:
        if not curriculum:
            return
        base = cur_lesson_i if cur_lesson_i is not None else 0
        switch_lesson(base + delta)

    def print_lesson_list() -> None:
        if not curriculum:
            log("[lesson] no curriculum")
            return
        log("[lesson] ——— curriculum ———")
        for line in format_lesson_list(curriculum).splitlines():
            log(line, also_print=True)
        if cur_lesson_i is not None:
            les = curriculum[cur_lesson_i]
            log(f"[lesson] current: {les.index} {les.id}")

    def scroll_at(
        pos: tuple[int, int],
        direction: int,
        code_rect: Any,
        console_rect: Any,
        *,
        horizontal: bool = False,
    ) -> None:
        """direction > 0 scrolls content down/right; wheel-up passes negative."""
        nonlocal console_scroll, console_follow
        if fs_mode == _FS_SHADER or direction == 0:
            return
        if code_rect.width and code_rect.collidepoint(pos):
            if horizontal:
                step = max(12, code_font.size("M")[0] * 4) * max(1, abs(direction))
                delta = step if direction > 0 else -step
                editor.scroll_x = max(0, editor.scroll_x + delta)
            else:
                step = _code_line_height(code_font) * max(1, abs(direction))
                delta = step if direction > 0 else -step
                editor.scroll_y = max(0, editor.scroll_y + delta)
        elif console_rect.width and console_rect.collidepoint(pos) and not horizontal:
            step = _console_line_height(font) * max(1, abs(direction))
            delta = step if direction > 0 else -step
            console_follow = False
            console_scroll = max(0, console_scroll + delta)

    def draw_title_bar(
        target: Any,
        title_rect: Any,
        close_btn: Any,
        *,
        close_pressed: bool,
        phase: float = 0.0,
    ) -> None:
        if not title_rect.width:
            return
        _draw_frosted_title_bar(target, pygame, title_rect)
        _draw_bevel_rect(
            target,
            pygame,
            title_rect,
            inset=False,
            thickness=1,
            corner_r=min(7, title_rect.height // 2),
            specular=True,
        )
        _draw_traffic_lights(
            target, pygame, title_rect, close_pressed=close_pressed
        )
        star = "*" if editor.dirty else ""
        title = f"VERNACULAR — {lesson_title_bit()}{shader.name}{star}::{entry}"
        label_x = title_rect.x + _traffic_cluster_width()
        # Measure with plain render for vertical centering.
        probe = title_font.render(title, True, _TITLE_TEXT)
        label_y = title_rect.y + (title_rect.height - probe.get_height()) // 2
        max_w = max(40, title_rect.right - label_x - 10)
        if probe.get_width() > max_w:
            # Truncate visually if the title is too long for the bar.
            while title and title_font.size(title + "…")[0] > max_w:
                title = title[:-1]
            title = title + "…"
        _draw_iridescent_title(
            target,
            pygame,
            title_font,
            title,
            label_x,
            label_y,
            phase=phase,
            font_hi=title_font_hi,
        )

    running = True
    last_poll = 0.0
    mouse_dragging = False  # legacy wobble poke (non-hwnd)
    hwnd_dragging = False
    shader_look_dragging = False  # primary drag updates mouse uniforms
    code_selecting = False
    last_mouse = (0, 0)
    last_cursor_screen: tuple[int, int] | None = None
    pygame.key.set_repeat(400, 35)

    def begin_hwnd_drag(pos: tuple[int, int], *, impulse: float | None = None) -> None:
        nonlocal hwnd_dragging, last_cursor_screen
        editor.focused = False
        hwnd_dragging = True
        last_cursor_screen = _cursor_screen_pos()
        if impulse is not None and wobble.enabled and fs_mode is None:
            wobble.impulse(impulse, bias=pos[0] * 0.01)

    def update_shader_mouse_from_pos(pos: tuple[int, int], *, down: bool) -> None:
        nonlocal mouse_xy, mouse_dxy, mouse_btn, shader_frame_dirty
        mx, my = _map_pos_to_shader_mouse(pos, img_rect, width, height)
        mouse_dxy = (mx - mouse_xy[0], my - mouse_xy[1])
        mouse_xy = (mx, my)
        mouse_btn = 1 if down else 0
        shader_frame_dirty = True

    while running:
        dt = clock.get_time() / 1000.0
        (
            title_rect,
            img_rect,
            btn_bar,
            code_rect,
            lesson_rect,
            color_rect,
            console_rect,
            content_rect,
            save_btn,
            reload_btn,
            prev_btn,
            next_btn,
            close_btn,
            amber_btn,
            green_btn,
            cyan_btn,
        ) = layout()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and fs_mode is None:
                # event size is the full display (includes wobble pad when shaped).
                new_cw = max(min_cw, int(event.w) - 2 * pad_x)
                new_ch = max(min_ch, int(event.h))
                apply_client_size(new_cw, new_ch, from_event=True)
            elif event.type == pygame.KEYDOWN:
                mods = event.mod
                ctrl = bool(mods & (pygame.KMOD_CTRL | pygame.KMOD_META))
                shift = bool(mods & pygame.KMOD_SHIFT)
                if event.key == pygame.K_ESCAPE:
                    if fs_mode is not None:
                        set_fs_mode(None)
                    else:
                        running = False
                elif ctrl and event.key == pygame.K_s:
                    do_save()
                elif ctrl and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    try_recompile(reason="ctrl+enter")
                elif event.key == pygame.K_F10 or (
                    event.key == pygame.K_F11 and shift
                ):
                    toggle_shader_fs()
                elif event.key == pygame.K_F11 or (
                    event.key == pygame.K_f and not editor.focused
                ):
                    toggle_window_fs()
                elif event.key == pygame.K_w and not editor.focused:
                    wobble.enabled = not wobble.enabled
                    state = "on" if wobble.enabled else "off"
                    log(f"[wobble] {state}")
                    if wobble.enabled and fs_mode is None:
                        wobble.impulse(0.9)
                elif event.key == pygame.K_q and not editor.focused:
                    running = False
                elif curriculum and (
                    (
                        ctrl
                        and event.key
                        in (
                            pygame.K_LEFTBRACKET,
                            pygame.K_RIGHTBRACKET,
                            pygame.K_LEFT,
                            pygame.K_RIGHT,
                            pygame.K_PAGEUP,
                            pygame.K_PAGEDOWN,
                        )
                    )
                    or (
                        not editor.focused
                        and event.key
                        in (
                            pygame.K_LEFTBRACKET,
                            pygame.K_RIGHTBRACKET,
                            pygame.K_LEFT,
                            pygame.K_RIGHT,
                            pygame.K_PAGEUP,
                            pygame.K_PAGEDOWN,
                            pygame.K_l,
                        )
                    )
                ):
                    if event.key in (
                        pygame.K_LEFTBRACKET,
                        pygame.K_LEFT,
                        pygame.K_PAGEUP,
                    ):
                        lesson_delta(-1)
                    elif event.key in (
                        pygame.K_RIGHTBRACKET,
                        pygame.K_RIGHT,
                        pygame.K_PAGEDOWN,
                    ):
                        lesson_delta(1)
                    elif event.key == pygame.K_l:
                        print_lesson_list()
                elif (
                    not editor.focused
                    and curriculum
                    and pygame.K_0 <= event.key <= pygame.K_9
                ):
                    switch_lesson(event.key - pygame.K_0)
                elif editor.focused and fs_mode != _FS_SHADER:
                    before_text = editor.get_text()
                    before_dirty = editor.dirty
                    if editor.handle_key(event, pygame):
                        code_view_h = max(1, code_rect.height - 2 * _PANEL_PAD)
                        code_view_w = max(1, code_rect.width - 2 * _PANEL_PAD)
                        editor.ensure_cursor_visible(
                            _code_line_height(code_font),
                            code_view_h,
                            code_font,
                            code_view_w,
                        )
                        if editor.get_text() != before_text:
                            schedule_edit_recompile()
                        elif editor.dirty != before_dirty:
                            caption()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicks = int(event.dict.get("clicks", 1) or 1)
                    alt = bool(pygame.key.get_mods() & pygame.KMOD_ALT)
                    if close_btn.width and close_btn.collidepoint(event.pos):
                        pressed_btn = "close"
                        running = False
                    elif green_btn.width and green_btn.collidepoint(event.pos):
                        # Traffic green ≈ window / IDE chrome fullscreen.
                        pressed_btn = "green"
                        toggle_window_fs()
                    elif cyan_btn.width and cyan_btn.collidepoint(event.pos):
                        # Traffic cyan ≈ shader-only fullscreen.
                        pressed_btn = "cyan"
                        toggle_shader_fs()
                    elif amber_btn.width and amber_btn.collidepoint(event.pos):
                        # Traffic yellow: decorative / reserved (no minimize on borderless).
                        pressed_btn = "amber"
                        log("[chrome] yellow — no minimize on borderless window")
                    elif save_btn.width and save_btn.collidepoint(event.pos):
                        pressed_btn = "save"
                        do_save()
                    elif reload_btn.width and reload_btn.collidepoint(event.pos):
                        pressed_btn = "reload"
                        do_reload_from_disk()
                    elif prev_btn.width and prev_btn.collidepoint(event.pos):
                        pressed_btn = "prev"
                        lesson_delta(-1)
                    elif next_btn.width and next_btn.collidepoint(event.pos):
                        pressed_btn = "next"
                        lesson_delta(1)
                    elif school_bufs and any(
                        tr.width and tr.collidepoint(event.pos) for _, tr in school_tab_rects
                    ):
                        for ti, tr in school_tab_rects:
                            if tr.width and tr.collidepoint(event.pos):
                                switch_school_tab(ti)
                                break
                    elif (
                        lesson_rect.width
                        and lesson_rect.collidepoint(event.pos)
                    ):
                        editor.focused = False
                    elif (
                        color_rect.width
                        and color_rect.collidepoint(event.pos)
                        and color_uniforms.active
                    ):
                        editor.focused = False
                        hit = _color_panel_hit(event.pos, color_hits)
                        if hit is None:
                            pass
                        elif hit.startswith("swatch:"):
                            color_uniforms.select_index(int(hit.split(":", 1)[1]))
                            shader_frame_dirty = True
                        else:
                            color_uniforms.drag = hit
                            if _color_panel_apply_drag(
                                color_uniforms, color_hits, event.pos, hit
                            ):
                                shader_frame_dirty = True
                    elif (
                        title_rect.width
                        and title_rect.collidepoint(event.pos)
                        and fs_mode is None
                    ):
                        # Custom title bar: move HWND + Compiz jello on drag.
                        begin_hwnd_drag(event.pos)
                    elif (
                        img_rect.width
                        and img_rect.collidepoint(event.pos)
                        and fs_mode != _FS_SHADER
                    ):
                        editor.focused = False
                        if clicks >= 2:
                            toggle_shader_fs()
                        elif fs_mode is None and alt:
                            # Alt+drag on shader: move window (even on interactive lessons).
                            begin_hwnd_drag(event.pos, impulse=0.35)
                        elif interactive_mouse:
                            # Primary drag: look / mouse uniforms — not window drag.
                            shader_look_dragging = True
                            update_shader_mouse_from_pos(event.pos, down=True)
                        elif fs_mode is None:
                            begin_hwnd_drag(event.pos, impulse=0.35)
                    elif (
                        img_rect.width
                        and img_rect.collidepoint(event.pos)
                        and fs_mode == _FS_SHADER
                        and interactive_mouse
                    ):
                        editor.focused = False
                        if clicks >= 2:
                            set_fs_mode(None)
                        else:
                            shader_look_dragging = True
                            update_shader_mouse_from_pos(event.pos, down=True)
                    elif (
                        img_rect.width
                        and img_rect.collidepoint(event.pos)
                        and fs_mode == _FS_SHADER
                        and clicks >= 2
                    ):
                        set_fs_mode(None)
                    elif code_rect.width and code_rect.collidepoint(event.pos):
                        code_view_h = max(1, code_rect.height - 2 * _PANEL_PAD)
                        code_view_w = max(1, code_rect.width - 2 * _PANEL_PAD)
                        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                        editor.click_at(
                            event.pos[0] - code_rect.x,
                            event.pos[1] - code_rect.y,
                            code_font,
                            _code_line_height(code_font),
                            code_view_h,
                            code_view_w,
                            panel_pad=_PANEL_PAD,
                            extend=shift,
                            double=clicks >= 2,
                        )
                        code_selecting = clicks < 2
                        if color_uniforms.active:
                            hit = editor.word_at(
                                event.pos[0] - code_rect.x,
                                event.pos[1] - code_rect.y,
                                code_font,
                                _code_line_height(code_font),
                                _PANEL_PAD,
                            )
                            if hit is not None:
                                word, row, col0 = hit
                                line = (
                                    editor.lines[row]
                                    if row < len(editor.lines)
                                    else ""
                                )
                                _focus_color_from_token(
                                    color_uniforms, word, line, col0
                                )
                    elif console_rect.width and console_rect.collidepoint(event.pos):
                        # Console: scroll only — never start window / wobble drag.
                        editor.focused = False
                    elif clicks >= 2:
                        if fs_mode is not None:
                            set_fs_mode(None)
                        else:
                            toggle_window_fs()
                    else:
                        # Chrome / letterbox gutters: unfocus editor, no window drag.
                        editor.focused = False
                elif event.button == 2:
                    # Middle-button on shader (or anywhere): window drag.
                    if fs_mode is None:
                        begin_hwnd_drag(event.pos, impulse=0.25)
                elif event.button == 4:
                    mods = pygame.key.get_mods()
                    scroll_at(
                        event.pos,
                        -1,
                        code_rect,
                        console_rect,
                        horizontal=bool(mods & pygame.KMOD_SHIFT),
                    )
                elif event.button == 5:
                    mods = pygame.key.get_mods()
                    scroll_at(
                        event.pos,
                        1,
                        code_rect,
                        console_rect,
                        horizontal=bool(mods & pygame.KMOD_SHIFT),
                    )
            elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 2):
                mouse_dragging = False
                if code_selecting and event.button == 1:
                    editor.end_mouse_select()
                    code_selecting = False
                if shader_look_dragging and event.button == 1:
                    shader_look_dragging = False
                    mouse_btn = 0
                    mouse_dxy = (0.0, 0.0)
                    shader_frame_dirty = True
                if color_uniforms.drag is not None and event.button == 1:
                    color_uniforms.drag = None
                if hwnd_dragging:
                    hwnd_dragging = False
                    wobble._dragging_window = False
                    last_cursor_screen = None
                pressed_btn = None
            elif event.type == pygame.MOUSEMOTION and code_selecting:
                if code_rect.width:
                    code_view_h = max(1, code_rect.height - 2 * _PANEL_PAD)
                    code_view_w = max(1, code_rect.width - 2 * _PANEL_PAD)
                    editor.drag_to(
                        event.pos[0] - code_rect.x,
                        event.pos[1] - code_rect.y,
                        code_font,
                        _code_line_height(code_font),
                        code_view_h,
                        code_view_w,
                        panel_pad=_PANEL_PAD,
                    )
            elif (
                event.type == pygame.MOUSEMOTION
                and not code_selecting
                and not hwnd_dragging
                and not shader_look_dragging
                and color_uniforms.drag is None
                and color_uniforms.active
                and code_rect.width
                and code_rect.collidepoint(event.pos)
                and fs_mode != _FS_SHADER
            ):
                hit = editor.word_at(
                    event.pos[0] - code_rect.x,
                    event.pos[1] - code_rect.y,
                    code_font,
                    _code_line_height(code_font),
                    _PANEL_PAD,
                )
                if hit is not None:
                    word, row, col0 = hit
                    line = editor.lines[row] if row < len(editor.lines) else ""
                    if _focus_color_from_token(color_uniforms, word, line, col0):
                        # Focus change only — no recompile; panel redraws next frame.
                        pass
            elif event.type == pygame.MOUSEMOTION and shader_look_dragging:
                update_shader_mouse_from_pos(event.pos, down=True)
            elif (
                event.type == pygame.MOUSEMOTION
                and color_uniforms.drag is not None
            ):
                if _color_panel_apply_drag(
                    color_uniforms,
                    color_hits,
                    event.pos,
                    color_uniforms.drag,
                ):
                    shader_frame_dirty = True
            elif event.type == pygame.MOUSEMOTION and hwnd_dragging:
                cur = _cursor_screen_pos()
                if cur is not None and last_cursor_screen is not None:
                    sdx = cur[0] - last_cursor_screen[0]
                    sdy = cur[1] - last_cursor_screen[1]
                    if sdx or sdy:
                        if shaped is not None and shaped.active:
                            shaped.move_by(sdx, sdy)
                        else:
                            # Borderless without shaped host: still try SDL move.
                            getter = getattr(pygame.display, "get_window_position", None)
                            setter = getattr(pygame.display, "set_window_position", None)
                            if callable(getter) and callable(setter):
                                px, py = getter()
                                setter((px + sdx, py + sdy))
                        if wobble.enabled and fs_mode is None:
                            wobble.poke_from_window_delta(float(sdx), float(sdy))
                        # Keep poll baseline in sync so we don't double-impulse.
                        if shaped is not None:
                            pos = shaped.get_pos()
                            if pos is not None:
                                wobble._last_win_pos = pos
                        last_cursor_screen = cur
            elif event.type == pygame.MOUSEMOTION and mouse_dragging:
                dx = event.pos[0] - last_mouse[0]
                last_mouse = event.pos
                if fs_mode is None:
                    wobble.poke_from_dx(float(dx), strong=False)
            elif event.type == pygame.MOUSEWHEEL:
                mods = pygame.key.get_mods()
                # Prefer explicit horizontal wheel when present; Shift+wheel otherwise.
                if getattr(event, "x", 0):
                    scroll_at(
                        pygame.mouse.get_pos(),
                        int(event.x),
                        code_rect,
                        console_rect,
                        horizontal=True,
                    )
                elif event.y:
                    scroll_at(
                        pygame.mouse.get_pos(),
                        -int(event.y),
                        code_rect,
                        console_rect,
                        horizontal=bool(mods & pygame.KMOD_SHIFT),
                    )

        now = time.monotonic()
        if need_reload:
            try_recompile(reason="start")
        elif edit_recompile_at is not None and now >= edit_recompile_at:
            try_recompile(reason="edit")
        elif (now - last_poll) >= poll_s:
            last_poll = now
            # If real file changed externally and buffer is clean, reload from disk.
            watch = school_bufs[school_i]["path"] if school_bufs else shader
            cur_real = _file_mtime(watch)
            if not editor.dirty and cur_real != real_mtime and cur_real >= 0:
                log("[disk] real file changed (editor clean) — reloading")
                do_reload_from_disk(discard_dirty=False)

        if module is not None and status == "ok":
            # Re-render when the entry samples time/mouse, or after hotswap / color edit.
            if entry_has_time or entry_has_mouse or shader_frame_dirty:
                try:
                    elapsed = time.perf_counter() - t0
                    last_ok = render_frame(
                        module,
                        entry,
                        width,
                        height,
                        time_s=elapsed,
                        mouse=mouse_xy,
                        mouse_delta=mouse_dxy,
                        mouse_down=mouse_btn,
                        colors=color_uniforms,
                        textures=lesson_textures,
                    )
                    shader_frame_dirty = False
                    frame_surf = None
                    if mouse_dxy != (0.0, 0.0) and not shader_look_dragging:
                        mouse_dxy = (0.0, 0.0)
                except Exception as exc:  # noqa: BLE001
                    status = "error"
                    last_error = f"{type(exc).__name__}: {exc}"
                    log(f"[frame] FAILED: {last_error}")
                    traceback.print_exc()
                    wobble.impulse(0.9)

        # OS window move → jello (skip while custom title-bar drag owns impulses).
        if fs_mode is None and wobble.enabled and not hwnd_dragging:
            wpos = None
            if shaped is not None and shaped.active:
                wpos = shaped.get_pos()
            if wpos is None:
                wpos = _window_pos(pygame)
            if wpos is not None:
                if wobble._last_win_pos is not None:
                    wdx = wpos[0] - wobble._last_win_pos[0]
                    wdy = wpos[1] - wobble._last_win_pos[1]
                    if abs(wdx) >= _WOBBLE_POS_EPS or abs(wdy) >= _WOBBLE_POS_EPS:
                        wobble.poke_from_window_delta(float(wdx), float(wdy))
                    else:
                        # Window stopped moving — let spring damp the jello out.
                        wobble._dragging_window = False
                wobble._last_win_pos = wpos

        if frame_surf is None:
            rgb = _light_sharpen_rgb(_to_uint8_rgb(last_ok))
            frame_surf = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
        frame = frame_surf

        # Compose: sharp UI canvas + optional jelly-warped shader preview overlay.
        if fs_mode is not None:
            canvas_size = screen.get_size()
        else:
            canvas_size = (content_w, content_h)
        if canvas_surf is None or canvas_surf.get_size() != canvas_size:
            canvas_surf = pygame.Surface(canvas_size)
        canvas = canvas_surf
        canvas.fill(_BEVEL_FACE)
        lay_w, lay_h = canvas_size

        if fs_mode == _FS_SHADER:
            scaled = frame
            if frame.get_size() != screen.get_size():
                scaled = pygame.transform.smoothscale(frame, screen.get_size())
            canvas.blit(scaled, (0, 0))
            # Minimal escape hint — dim, bottom-center; never covers look UX meaningfully.
            hint = font.render("Esc exit fullscreen", True, (160, 168, 180))
            hx = max(8, (lay_w - hint.get_width()) // 2)
            hy = max(8, lay_h - hint.get_height() - 12)
            canvas.blit(hint, (hx, hy))
            screen.blit(canvas, (0, 0))
        else:
            (
                title_rect,
                img_rect,
                btn_bar,
                code_rect,
                lesson_rect,
                color_rect,
                console_rect,
                content_rect,
                save_btn,
                reload_btn,
                prev_btn,
                next_btn,
                close_btn,
                amber_btn,
                green_btn,
                cyan_btn,
            ) = layout()

            # Layout rects are in screen/padded space; draw into content-local canvas.
            ox, oy = content_origin()

            def local(r: Any) -> Any:
                if r.width <= 0:
                    return r
                return pygame.Rect(r.x - ox, r.y - oy, r.width, r.height)

            t_local = local(title_rect)
            img_l = local(img_rect)
            btn_l = local(btn_bar)
            code_l = local(code_rect)
            lesson_l = local(lesson_rect)
            color_l = local(color_rect)
            cons_l = local(console_rect)
            content_l = local(content_rect)
            save_l = local(save_btn)
            reload_l = local(reload_btn)
            prev_l = local(prev_btn)
            next_l = local(next_btn)
            close_l = local(close_btn)

            draw_title_bar(
                canvas,
                t_local,
                close_l,
                close_pressed=pressed_btn == "close",
                phase=(time.perf_counter() - t0) * 0.12,
            )

            # Shader letterboxed into left column (scale-to-fit, keep aspect).
            if frame.get_size() != (img_l.width, img_l.height):
                scaled = pygame.transform.smoothscale(
                    frame, (img_l.width, img_l.height)
                )
            else:
                scaled = frame
            canvas.blit(scaled, img_l.topleft)

            # Button bar + filename (dirty star).
            pygame.draw.rect(canvas, _BEVEL_FACE, btn_l)
            _draw_button(
                canvas,
                pygame,
                btn_font,
                save_l,
                "Save",
                pressed=pressed_btn == "save",
            )
            _draw_button(
                canvas,
                pygame,
                btn_font,
                reload_l,
                "Reload",
                pressed=pressed_btn == "reload",
            )
            if prev_l.width:
                _draw_button(
                    canvas,
                    pygame,
                    btn_font,
                    prev_l,
                    "<",
                    pressed=pressed_btn == "prev",
                )
            if next_l.width:
                _draw_button(
                    canvas,
                    pygame,
                    btn_font,
                    next_l,
                    ">",
                    pressed=pressed_btn == "next",
                )
            for ti, tr in school_tab_rects:
                tl = local(tr)
                lab = str(school_bufs[ti]["label"]) if school_bufs else str(ti)
                if ti == school_i:
                    lab = f"[{lab}]"
                _draw_button(
                    canvas,
                    pygame,
                    btn_font,
                    tl,
                    lab,
                    pressed=ti == school_i,
                )
            star = "*" if editor.dirty else ""
            name_anchor = next_l.right if next_l.width else reload_l.right
            if school_tab_rects:
                name_anchor = max(name_anchor, local(school_tab_rects[-1][1]).right)
            shown_name = (
                school_bufs[school_i]["path"].name if school_bufs else shader.name
            )
            name_surf = btn_font.render(f"{shown_name}{star}", True, (176, 184, 198))
            name_x = name_anchor + _BTN_GAP + 4
            canvas.blit(
                name_surf,
                (name_x, btn_l.y + (_BTN_BAR_H - name_surf.get_height()) // 2),
            )

            if lesson_l.width and lesson_lines:
                _draw_lesson_strip(canvas, pygame, font, lesson_l, lesson_lines)
            if color_l.width and color_uniforms.active:
                # Draw in canvas-local; rebase hit regions to screen/padded space.
                local_hits = _draw_color_panel(
                    canvas, pygame, font, color_l, color_uniforms
                )
                color_hits.clear()
                color_hits["swatches"] = [
                    (
                        i,
                        pygame.Rect(
                            srect.x + ox, srect.y + oy, srect.width, srect.height
                        ),
                    )
                    for i, srect in local_hits.get("swatches", [])
                ]
                for key in ("sv", "hue"):
                    r = local_hits.get(key)
                    if r is not None and getattr(r, "width", 0):
                        color_hits[key] = pygame.Rect(
                            r.x + ox, r.y + oy, r.width, r.height
                        )
                    else:
                        color_hits[key] = r
                color_hits["sliders"] = [
                    (
                        ch,
                        pygame.Rect(
                            srect.x + ox, srect.y + oy, srect.width, srect.height
                        ),
                    )
                    for ch, srect in local_hits.get("sliders", [])
                ]
            else:
                color_hits.clear()
                color_hits.update(
                    {"swatches": [], "sv": None, "hue": None, "sliders": []}
                )

            line_h = _code_line_height(code_font)
            code_view_h = max(1, code_l.height - 2 * _PANEL_PAD)
            code_view_w = max(1, code_l.width - 2 * _PANEL_PAD)
            editor.scroll_y = min(
                editor.scroll_y,
                _max_scroll(len(editor.lines), line_h, code_view_h),
            )
            editor.scroll_x = min(
                editor.scroll_x,
                _max_scroll_x(editor.lines, code_font, code_view_w),
            )
            text_w = max(40, cons_l.width - 2 * _PANEL_PAD)
            n_console = _console_line_count(console_lines, font, text_w)
            max_c = _max_scroll(
                n_console, _console_line_height(font), cons_l.height, pad=_PANEL_PAD
            )
            if console_follow or console_scroll >= max_c:
                console_follow = True
                console_scroll = max_c
            else:
                console_scroll = min(console_scroll, max_c)

            caret_on = (pygame.time.get_ticks() // 530) % 2 == 0
            sel = editor.selection_range()
            code_key = (
                id(editor._tokens),
                editor.scroll_x,
                editor.scroll_y,
                editor.row,
                editor.col,
                sel,
                caret_on,
                code_l.width,
                code_l.height,
                editor.focused,
            )
            if (
                code_cache_surf is None
                or code_cache_key != code_key
                or code_cache_surf.get_size() != (code_l.width, code_l.height)
            ):
                if (
                    code_cache_surf is None
                    or code_cache_surf.get_size() != (code_l.width, code_l.height)
                ):
                    code_cache_surf = pygame.Surface((max(1, code_l.width), max(1, code_l.height)))
                _draw_code_panel(
                    code_cache_surf,
                    pygame,
                    code_font,
                    editor,
                    pygame.Rect(0, 0, code_l.width, code_l.height),
                    caret_on=caret_on,
                )
                code_cache_key = code_key
            canvas.blit(code_cache_surf, code_l.topleft)
            _draw_console(canvas, pygame, font, console_lines, cons_l, console_scroll)

            # Embossed chrome around body (below title bar).
            body_top = t_local.height if t_local.width else 0
            _draw_bevel_rect(
                canvas,
                pygame,
                pygame.Rect(0, body_top, lay_w, lay_h - body_top),
                inset=False,
                thickness=_CHROME,
                corner_r=0 if body_top else _CORNER_RADIUS,
            )
            # Soft outer silhouette corners (matches rounded HRGN when settled).
            if fs_mode is None:
                _mask_round_corners(
                    canvas, pygame, lay_w, lay_h, _CORNER_RADIUS, (0, 0, 0)
                )
            _draw_bevel_v_divider(
                canvas,
                pygame,
                code_l.x - _DIVIDER,
                content_l.y,
                max(
                    1,
                    (
                        lesson_l.y
                        if lesson_l.width
                        else (color_l.y if color_l.width else cons_l.y)
                    )
                    - content_l.y
                    - _DIVIDER,
                ),
                thickness=_DIVIDER,
                inset=True,
            )
            if lesson_l.width:
                _draw_bevel_h_divider(
                    canvas,
                    pygame,
                    content_l.x,
                    lesson_l.y - _DIVIDER,
                    content_l.width,
                    thickness=_DIVIDER,
                    inset=True,
                )
            if color_l.width:
                _draw_bevel_h_divider(
                    canvas,
                    pygame,
                    content_l.x,
                    color_l.y - _DIVIDER,
                    content_l.width,
                    thickness=_DIVIDER,
                    inset=True,
                )
            _draw_bevel_h_divider(
                canvas,
                pygame,
                content_l.x,
                cons_l.y - _DIVIDER,
                content_l.width,
                thickness=_DIVIDER,
                inset=True,
            )

            # Status / errors stay in the green console only — never overlay the shader.

            if fs_mode == _FS_WINDOW:
                # Window FS: full IDE chrome, no wobble / shaped silhouette.
                screen.blit(canvas, (0, 0))
            else:
                wobble.update(dt if dt > 0 else 1.0 / 60.0)
                fill = COLORKEY_RGB if (shaped is not None and shaped.mode == "colorkey") else (0, 0, 0)
                if shaped is not None and shaped.mode == "colorkey":
                    shaped.prepare_colorkey_surface(pygame, screen)

                # Full-frame jelly: shader + code + console warp together at full-res
                # nearest (identity blit when settled — no half-res / smoothscale).
                wobble.blit(
                    pygame,
                    screen,
                    canvas,
                    origin_x=pad_x,
                    fill_color=fill,
                )

                # Drive OS silhouette from mesh left/right edge curves (Windows).
                if shaped is not None and shaped.mode == "rgn":
                    edge_ys, left_ox, right_ox = wobble.edge_curves(
                        content_w, content_h
                    )
                    shaped.apply_mesh_silhouette(
                        edge_ys,
                        left_ox,
                        right_ox,
                        content_w=content_w,
                        content_h=content_h,
                        origin_x=pad_x,
                        origin_y=0,
                        corner_r=_CORNER_RADIUS,
                    )

        pygame.display.flip()
        clock.tick(60)

    if shaped is not None:
        shaped.clear_region()
    pygame.quit()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="VERNACULAR — live SlangPy preview (in-window edit, temp hotswap, Save to disk)"
    )
    p.add_argument(
        "--shader",
        type=Path,
        default=None,
        help="Path to .slang module (default: first curriculum lesson)",
    )
    p.add_argument(
        "--lesson",
        type=str,
        default=None,
        help="Curriculum lesson index or id (e.g. 0, bos/00_hello, neural/n01_function_to_network)",
    )
    p.add_argument(
        "--entry",
        type=str,
        default=None,
        help="Entry function name (default: from lesson or hello_pixel)",
    )
    p.add_argument(
        "--size",
        type=int,
        default=_DEFAULT_LIVE_SIZE,
        help=f"Square render size / default window scale (default: {_DEFAULT_LIVE_SIZE})",
    )
    p.add_argument("--width", type=int, default=None, help="Override width (default: --size)")
    p.add_argument("--height", type=int, default=None, help="Override height (default: --size)")
    p.add_argument(
        "--once",
        action="store_true",
        help="Render one frame and exit (no window; useful for smoke / headless)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="With --once, optional PNG output path",
    )
    p.add_argument(
        "--time",
        type=float,
        default=0.0,
        help="With --once (or as initial live clock offset), seconds passed as float time",
    )
    p.add_argument(
        "--files",
        nargs="+",
        type=Path,
        default=None,
        help="Open multiple .slang files as editor tabs (VS / PS / Diff school)",
    )
    p.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Comma labels matching --files (e.g. VS,PS,Diff)",
    )
    p.add_argument(
        "--no-curriculum",
        action="store_true",
        help="Do not load lesson bank (keep --files tabs)",
    )
    p.add_argument(
        "--school-3d",
        action="store_true",
        help="Temple 3D school window: stable caption, no curriculum nav",
    )
    args = p.parse_args(argv)

    width = args.width or args.size
    height = args.height or args.size

    curriculum = load_curriculum()
    lesson: Lesson | None = None
    lesson_index: int | None = None
    school_tabs: list[tuple[str, Path]] | None = None
    if args.files:
        labels = (
            [x.strip() for x in args.labels.split(",")]
            if args.labels
            else [p.stem for p in args.files]
        )
        while len(labels) < len(args.files):
            labels.append(args.files[len(labels)].stem)
        school_tabs = [
            (labels[i], _resolve_shader(args.files[i])) for i in range(len(args.files))
        ]
        preview = school_tabs[-1][1]
        for lab, pth in school_tabs:
            if pth.name.endswith("_diff.slang"):
                preview = pth
                break
        shader = preview
        entry = args.entry or "hello_pixel"
        if args.no_curriculum or args.school_3d:
            curriculum = []
            lesson_index = None
    elif args.lesson is not None:
        lesson = find_lesson(args.lesson, curriculum)
        lesson_index = lesson.index
        shader = lesson.shader
        entry = args.entry or lesson.entry
    elif args.shader is not None:
        shader = _resolve_shader(args.shader)
        entry = args.entry or "hello_pixel"
    elif curriculum:
        lesson = curriculum[0]
        lesson_index = 0
        shader = lesson.shader
        entry = args.entry or lesson.entry
    else:
        shader = _resolve_shader(SLANG_DIR / "lab_kernels.slang")
        entry = args.entry or "hello_pixel"

    if args.once:
        tex = lesson.texture if lesson is not None else None
        run_once(
            shader, entry, width, height, out=args.out, time_s=args.time, texture=tex
        )
        tag = f"lesson {lesson.id}" if lesson else shader.name
        print(f"Rendered {width}x{height} via {tag}::{entry}")
        return 0

    return run_live(
        shader,
        entry,
        width,
        height,
        lessons=curriculum,
        lesson_index=lesson_index,
        school_tabs=school_tabs,
        school_3d=bool(args.school_3d or school_tabs),
    )


if __name__ == "__main__":
    raise SystemExit(main())

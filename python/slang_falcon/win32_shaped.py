"""Windows shaped / borderless host for Compiz-style window silhouette wobble.

Primary path: borderless HWND + ``SetWindowRgn`` from a closed polygon whose
left/right sides follow the jelly mesh displacement-field edge curves (dense
polyline samples), so the OS outline matches the warped pixels.

Fallback: borderless + pygame color-key transparency if region APIs fail.

Non-Windows callers should not use this module; ``live.py`` keeps a normal
rectangular window elsewhere.
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass
from typing import Any, Sequence

# Magenta colorkey for the borderless fallback (unlikely in UI chrome).
COLORKEY_RGB = (255, 0, 255)

_GWL_EXSTYLE = -20
_WS_EX_LAYERED = 0x00080000
_LWA_COLORKEY = 0x00000001
_SWP_NOSIZE = 0x0001
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_WINDING = 2

_DEFAULT_CORNER_R = 8
_SETTLED_QX = 0
# Cap CreatePolygonRgn / SetWindowRgn while deforming (~30 Hz). Settled
# transitions always apply immediately (sharp round-rect restore).
_RGN_MIN_INTERVAL_S = 1.0 / 30.0
# Quantize edge offsets so tiny mesh jitter doesn't rebuild HRGN every frame.
_RGN_QUANT_PX = 2


@dataclass
class ShapedHostInfo:
    """Result of enabling the Windows shaped host."""

    mode: str  # "rgn" | "colorkey" | "none"
    hwnd: int
    pad_x: int
    detail: str = ""


class Win32ShapedHost:
    """Borderless pygame HWND with mesh-driven window region (or colorkey)."""

    def __init__(self, pad_x: int) -> None:
        self.pad_x = max(0, int(pad_x))
        self.hwnd = 0
        self.mode = "none"
        self.detail = ""
        self._user32: Any = None
        self._gdi32: Any = None
        self._last_rgn_key: tuple[Any, ...] | None = None
        self._last_rgn_time: float = 0.0
        self._point_cls: Any = None

    @property
    def active(self) -> bool:
        return self.mode in ("rgn", "colorkey") and self.hwnd != 0

    def attach(self, pygame: Any) -> ShapedHostInfo:
        """Read HWND after ``set_mode`` and enable shaped / colorkey path."""
        if sys.platform != "win32":
            return ShapedHostInfo("none", 0, self.pad_x, "not Windows")

        import ctypes
        from ctypes import wintypes

        self._user32 = ctypes.windll.user32
        self._gdi32 = ctypes.windll.gdi32

        class POINT(ctypes.Structure):
            _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

        self._point_cls = POINT

        info = pygame.display.get_wm_info()
        hwnd = int(info.get("window") or 0)
        if not hwnd:
            self.mode = "none"
            self.detail = "no HWND from pygame"
            return ShapedHostInfo(self.mode, 0, self.pad_x, self.detail)

        self.hwnd = hwnd

        # Prefer SetWindowRgn (plays with pygame.display.flip).
        try:
            empty = self._gdi32.CreateRectRgn(0, 0, 1, 1)
            if not empty:
                raise OSError("CreateRectRgn failed")
            ok = self._user32.SetWindowRgn(hwnd, empty, True)
            if not ok:
                self._gdi32.DeleteObject(empty)
                raise OSError(f"SetWindowRgn failed ({ctypes.GetLastError()})")
            # System owns `empty` after success — seed a full-client region next frame.
            self.mode = "rgn"
            self.detail = "SetWindowRgn jelly edge-curve silhouette"
            self._last_rgn_key = None
            self._last_rgn_time = 0.0
            return ShapedHostInfo(self.mode, hwnd, self.pad_x, self.detail)
        except Exception as exc:  # noqa: BLE001
            rgn_err = str(exc)

        # Fallback: WS_EX_LAYERED + color key.
        try:
            get_long = self._user32.GetWindowLongW
            set_long = self._user32.SetWindowLongW
            ex = int(get_long(hwnd, _GWL_EXSTYLE))
            set_long(hwnd, _GWL_EXSTYLE, ex | _WS_EX_LAYERED)
            ck = (COLORKEY_RGB[0] << 16) | (COLORKEY_RGB[1] << 8) | COLORKEY_RGB[2]
            if not self._user32.SetLayeredWindowAttributes(hwnd, ck, 0, _LWA_COLORKEY):
                raise OSError(f"SetLayeredWindowAttributes failed ({ctypes.GetLastError()})")
            self.mode = "colorkey"
            self.detail = (
                f"SetWindowRgn failed ({rgn_err}); using layered color-key fallback "
                f"(pads transparent; outline still mostly rectangular)"
            )
            return ShapedHostInfo(self.mode, hwnd, self.pad_x, self.detail)
        except Exception as exc:  # noqa: BLE001
            self.mode = "none"
            self.detail = f"shaped host unavailable: rgn={rgn_err}; colorkey={exc}"
            return ShapedHostInfo(self.mode, hwnd, self.pad_x, self.detail)

    def clear_region(self) -> None:
        """Remove custom region (fullscreen / teardown)."""
        if self.mode != "rgn" or not self.hwnd or not self._user32:
            return
        self._user32.SetWindowRgn(self.hwnd, None, True)
        self._last_rgn_key = None
        self._last_rgn_time = 0.0

    def apply_strip_silhouette(
        self,
        offsets: Sequence[float],
        *,
        content_w: int,
        content_h: int,
        origin_x: int,
        origin_y: int,
        corner_r: int = _DEFAULT_CORNER_R,
    ) -> None:
        """Compatibility wrapper — same offset on both edges (pure shear)."""
        n = len(offsets)
        if n <= 0:
            return
        ys = [int(round(i * (content_h - 1) / max(1, n - 1))) for i in range(n)]
        self.apply_mesh_silhouette(
            ys,
            offsets,
            offsets,
            content_w=content_w,
            content_h=content_h,
            origin_x=origin_x,
            origin_y=origin_y,
            corner_r=corner_r,
        )

    def apply_mesh_silhouette(
        self,
        ys: Sequence[int],
        left_offsets: Sequence[float],
        right_offsets: Sequence[float],
        *,
        content_w: int,
        content_h: int,
        origin_x: int,
        origin_y: int,
        corner_r: int = _DEFAULT_CORNER_R,
    ) -> None:
        """Set window region from smooth left/right mesh edge curves.

        When settled, uses ``CreateRoundRectRgn``. While deforming, builds
        ``CreatePolygonRgn`` from displacement-field edge samples, rate-limited
        and quantized so silhouette stays close without rebuilding every frame.
        """
        if self.mode != "rgn" or not self.hwnd or not self._gdi32 or not self._user32:
            return
        if content_w <= 0 or content_h <= 0 or len(ys) < 2:
            return
        if len(left_offsets) != len(ys) or len(right_offsets) != len(ys):
            return

        q = max(1, int(_RGN_QUANT_PX))

        def _q(v: float) -> int:
            return int(round(float(v) / q)) * q

        left_i = tuple(_q(x) for x in left_offsets)
        right_i = tuple(_q(x) for x in right_offsets)
        ys_i = tuple(int(y) for y in ys)
        settled = max(max(abs(v) for v in left_i), max(abs(v) for v in right_i)) <= _SETTLED_QX
        cr = max(0, min(int(corner_r), content_w // 2, content_h // 2))
        key = (content_w, content_h, origin_x, origin_y, cr, ys_i, left_i, right_i)
        if key == self._last_rgn_key:
            return

        now = time.monotonic()
        # Always apply immediately when becoming settled (or first key); otherwise
        # throttle polygon rebuilds while the jelly is moving.
        if (
            not settled
            and self._last_rgn_key is not None
            and (now - self._last_rgn_time) < _RGN_MIN_INTERVAL_S
        ):
            return

        if settled and cr > 0:
            rgn = self._gdi32.CreateRoundRectRgn(
                origin_x,
                origin_y,
                origin_x + content_w,
                origin_y + content_h,
                cr * 2,
                cr * 2,
            )
        else:
            # No corner fillet while deforming — keep HRGN flush with warped edges.
            rgn = self._polygon_rgn_from_edges(
                ys_i,
                left_i,
                right_i,
                content_w=content_w,
                origin_x=origin_x,
                origin_y=origin_y,
                corner_r=0,
            )
        if not rgn:
            return

        if self._user32.SetWindowRgn(self.hwnd, rgn, True):
            self._last_rgn_key = key
            self._last_rgn_time = now
        else:
            self._gdi32.DeleteObject(rgn)

    def _polygon_rgn_from_edges(
        self,
        ys: Sequence[int],
        left_ox: Sequence[int],
        right_ox: Sequence[int],
        *,
        content_w: int,
        origin_x: int,
        origin_y: int,
        corner_r: int,
    ) -> int:
        """Closed path: top, right curve down, bottom, left curve up."""
        import ctypes

        point_cls = self._point_cls
        if point_cls is None:
            return 0

        left: list[tuple[int, int]] = []
        right: list[tuple[int, int]] = []
        for y, lox, rox in zip(ys, left_ox, right_ox):
            left.append((origin_x + int(lox), origin_y + int(y)))
            right.append((origin_x + content_w + int(rox), origin_y + int(y)))

        if corner_r > 0 and len(left) >= 2:
            left, right = _fillet_vertical_edges(left, right, corner_r)

        # Top (L→R), right (top→bottom), bottom (R→L), left (bottom→top).
        # Equivalently: right down + left reversed (connections form top/bottom).
        coords = right + list(reversed(left))
        count = len(coords)
        if count < 3:
            return 0

        arr = (point_cls * count)(*coords)
        return int(self._gdi32.CreatePolygonRgn(ctypes.byref(arr), count, _WINDING))

    def get_pos(self) -> tuple[int, int] | None:
        if not self.hwnd or not self._user32:
            return None
        from ctypes import wintypes
        import ctypes

        rect = wintypes.RECT()
        if self._user32.GetWindowRect(self.hwnd, ctypes.byref(rect)):
            return int(rect.left), int(rect.top)
        return None

    def move_by(self, dx: int, dy: int) -> tuple[int, int] | None:
        """Move HWND by (dx, dy). Returns new top-left or None."""
        pos = self.get_pos()
        if pos is None or not self._user32:
            return None
        x, y = pos[0] + int(dx), pos[1] + int(dy)
        self._user32.SetWindowPos(
            self.hwnd,
            None,
            x,
            y,
            0,
            0,
            _SWP_NOSIZE | _SWP_NOZORDER | _SWP_NOACTIVATE,
        )
        return x, y

    def prepare_colorkey_surface(self, pygame: Any, surface: Any) -> None:
        """Fill pads with colorkey and mark the display surface (fallback mode)."""
        if self.mode != "colorkey":
            return
        surface.set_colorkey(COLORKEY_RGB)


def _fillet_vertical_edges(
    left: list[tuple[int, int]],
    right: list[tuple[int, int]],
    corner_r: int,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Pull outline points near top/bottom toward a soft corner radius."""
    r = max(0, int(corner_r))
    if r <= 0 or len(left) < 3:
        return left, right

    def fillet_side(
        pts: list[tuple[int, int]], *, inward: int
    ) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        y0 = pts[0][1]
        y1 = pts[-1][1]
        for x, y in pts:
            d_top = y - y0
            d_bot = y1 - y
            inset = 0.0
            if d_top < r:
                t = 1.0 - (d_top / r)
                inset = max(inset, r * (1.0 - math.sqrt(max(0.0, 1.0 - t * t))))
            if d_bot < r:
                t = 1.0 - (d_bot / r)
                inset = max(inset, r * (1.0 - math.sqrt(max(0.0, 1.0 - t * t))))
            out.append((int(round(x + inward * inset)), y))
        return out

    return fillet_side(left, inward=1), fillet_side(right, inward=-1)


def wobble_pad_x(max_px: float) -> int:
    """Horizontal padding so displaced content stays inside the HWND."""
    return int(math.ceil(max_px)) + 1


def is_windows() -> bool:
    return sys.platform == "win32"

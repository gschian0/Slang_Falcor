"""In-window shader code editor: line buffer, undo/redo, selection, clipboard."""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, ClassVar

# Undo: coalesce rapid inserts until pause or a non-insert edit.
_UNDO_COALESCE_S = 0.4
_UNDO_MAX_DEPTH = 100

_WORD_RE = re.compile(r"[A-Za-z0-9_]+")

# Set by live.py to avoid circular imports (tokenize_slang lives there).
TokenizeFn = Callable[[str], list[list[tuple[str, str]]]]


@dataclass(frozen=True)
class EditorSnapshot:
    """Full editor restore point (buffer + caret + scroll)."""

    text: str
    row: int
    col: int
    scroll_y: int
    scroll_x: int


class EditorHistory:
    """Undo/redo stacks with insert coalescing.

    Rapid ``insert`` edits within ``coalesce_s`` share one undo entry (snapshot
    taken before the first keystroke of the chunk). Any other edit kind closes
    the chunk and pushes its own before-state. Depth is capped at ``max_depth``.
    """

    def __init__(
        self,
        *,
        max_depth: int = _UNDO_MAX_DEPTH,
        coalesce_s: float = _UNDO_COALESCE_S,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.max_depth = max(1, int(max_depth))
        self.coalesce_s = float(coalesce_s)
        self._clock = clock or time.monotonic
        self._undo: list[EditorSnapshot] = []
        self._redo: list[EditorSnapshot] = []
        self._coalesce_kind: str | None = None
        self._coalesce_deadline: float = 0.0

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._coalesce_kind = None
        self._coalesce_deadline = 0.0

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def record_before(self, snap: EditorSnapshot, kind: str) -> None:
        """Record state *before* an edit. ``kind=='insert'`` coalesces."""
        now = self._clock()
        if (
            kind == "insert"
            and self._coalesce_kind == "insert"
            and now < self._coalesce_deadline
            and self._undo
        ):
            self._coalesce_deadline = now + self.coalesce_s
            return
        self._undo.append(snap)
        if len(self._undo) > self.max_depth:
            overflow = len(self._undo) - self.max_depth
            del self._undo[:overflow]
        self._redo.clear()
        if kind == "insert":
            self._coalesce_kind = "insert"
            self._coalesce_deadline = now + self.coalesce_s
        else:
            self._coalesce_kind = None
            self._coalesce_deadline = 0.0

    def undo(self, current: EditorSnapshot) -> EditorSnapshot | None:
        self._coalesce_kind = None
        self._coalesce_deadline = 0.0
        if not self._undo:
            return None
        self._redo.append(current)
        return self._undo.pop()

    def redo(self, current: EditorSnapshot) -> EditorSnapshot | None:
        self._coalesce_kind = None
        self._coalesce_deadline = 0.0
        if not self._redo:
            return None
        self._undo.append(current)
        return self._redo.pop()


def clipboard_set(text: str, pygame: Any | None = None) -> bool:
    """Copy ``text`` to the system clipboard. Returns True on success."""
    payload = text.replace("\n", "\r\n") if sys.platform == "win32" else text
    if pygame is not None:
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            raw = payload.encode("utf-8")
            pygame.scrap.put(pygame.SCRAP_TEXT, raw)
            return True
        except Exception:  # noqa: BLE001
            pass
    if sys.platform == "win32":
        try:
            import ctypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            CF_UNICODETEXT = 13
            GMEM_MOVEABLE = 0x0002
            if not user32.OpenClipboard(None):
                return False
            try:
                user32.EmptyClipboard()
                data = payload.encode("utf-16-le") + b"\x00\x00"
                h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                if not h:
                    return False
                ptr = kernel32.GlobalLock(h)
                ctypes.memmove(ptr, data, len(data))
                kernel32.GlobalUnlock(h)
                if not user32.SetClipboardData(CF_UNICODETEXT, h):
                    kernel32.GlobalFree(h)
                    return False
                return True
            finally:
                user32.CloseClipboard()
        except Exception:  # noqa: BLE001
            return False
    return False


def clipboard_get(pygame: Any | None = None) -> str:
    """Read text from the system clipboard (may be empty)."""
    if pygame is not None:
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            data = pygame.scrap.get(pygame.SCRAP_TEXT)
            if data:
                if isinstance(data, bytes):
                    for enc in ("utf-8", "utf-16", "latin-1"):
                        try:
                            return data.decode(enc).replace("\x00", "").replace("\r\n", "\n")
                        except UnicodeDecodeError:
                            continue
                elif isinstance(data, str):
                    return data.replace("\r\n", "\n")
        except Exception:  # noqa: BLE001
            pass
    if sys.platform == "win32":
        try:
            import ctypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            CF_UNICODETEXT = 13
            if not user32.OpenClipboard(None):
                return ""
            try:
                h = user32.GetClipboardData(CF_UNICODETEXT)
                if not h:
                    return ""
                ptr = kernel32.GlobalLock(h)
                if not ptr:
                    return ""
                try:
                    text = ctypes.wstring_at(ptr)
                finally:
                    kernel32.GlobalUnlock(h)
                return text.replace("\r\n", "\n").replace("\r", "\n")
            finally:
                user32.CloseClipboard()
        except Exception:  # noqa: BLE001
            return ""
    return ""


def _word_bounds(line: str, col: int) -> tuple[int, int]:
    """Inclusive-start / exclusive-end of word under ``col`` (or nearby)."""
    if not line:
        return 0, 0
    col = max(0, min(col, len(line)))
    # Prefer character at col, else the one before (caret after word).
    probe = col if col < len(line) else max(0, col - 1)
    for m in _WORD_RE.finditer(line):
        if m.start() <= probe < m.end():
            return m.start(), m.end()
    return col, col


class CodeEditor:
    """Line-buffer text editor with undo, selection, and clipboard."""

    _tokenize_fn: ClassVar[TokenizeFn | None] = None

    def __init__(
        self,
        *,
        history: EditorHistory | None = None,
    ) -> None:
        self.lines: list[str] = [""]
        self.row = 0
        self.col = 0
        self.scroll_y = 0
        self.scroll_x = 0
        self.dirty = False
        self.focused = True
        self._tokens: list[list[tuple[str, str]]] = [[("", "default")]]
        self._saved_text = ""
        # Selection: anchor + caret (row,col). None = no selection.
        self.sel_anchor: tuple[int, int] | None = None
        self.history = history or EditorHistory()
        self._selecting = False  # mouse drag in progress

    # --- snapshots / dirty -------------------------------------------------

    def snapshot(self) -> EditorSnapshot:
        return EditorSnapshot(
            self.get_text(),
            self.row,
            self.col,
            self.scroll_y,
            self.scroll_x,
        )

    def restore(self, snap: EditorSnapshot) -> None:
        self._apply_text(snap.text)
        self.row = snap.row
        self.col = snap.col
        self.scroll_y = snap.scroll_y
        self.scroll_x = snap.scroll_x
        self.clear_selection()
        self._clamp_cursor()
        self._sync_dirty()
        self._retokenize()

    def _apply_text(self, text: str) -> None:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
        self.lines = normalized.split("\n") or [""]

    def _sync_dirty(self) -> None:
        self.dirty = self.get_text() != self._saved_text

    def mark_saved(self) -> None:
        self._saved_text = self.get_text()
        self.dirty = False

    def set_text(self, text: str, *, dirty: bool = False) -> None:
        self._apply_text(text)
        self.row = min(self.row, len(self.lines) - 1)
        self.col = min(self.col, len(self.lines[self.row]))
        self.clear_selection()
        if dirty:
            self._sync_dirty()
        else:
            self._saved_text = self.get_text()
            self.dirty = False
        self.history.clear()
        self._retokenize()

    def get_text(self) -> str:
        return "\n".join(self.lines)

    def _retokenize(self) -> None:
        fn = type(self)._tokenize_fn
        if fn is None:
            self._tokens = [[("", "default")] for _ in self.lines] or [[("", "default")]]
            return
        self._tokens = fn(self.get_text())

    def _mark_dirty(self) -> None:
        self._sync_dirty()
        self._retokenize()

    def _clamp_cursor(self) -> None:
        self.row = max(0, min(self.row, len(self.lines) - 1))
        self.col = max(0, min(self.col, len(self.lines[self.row])))

    def _record(self, kind: str) -> None:
        self.history.record_before(self.snapshot(), kind)

    # --- selection ---------------------------------------------------------

    def clear_selection(self) -> None:
        self.sel_anchor = None

    def has_selection(self) -> bool:
        if self.sel_anchor is None:
            return False
        ar, ac = self.sel_anchor
        return (ar, ac) != (self.row, self.col)

    def selection_range(self) -> tuple[int, int, int, int] | None:
        """Normalized (r0, c0, r1, c1) with (r0,c0) <= (r1,c1), or None."""
        if not self.has_selection() or self.sel_anchor is None:
            return None
        a = self.sel_anchor
        b = (self.row, self.col)
        if a <= b:
            return a[0], a[1], b[0], b[1]
        return b[0], b[1], a[0], a[1]

    def get_selected_text(self) -> str:
        rng = self.selection_range()
        if rng is None:
            return ""
        r0, c0, r1, c1 = rng
        if r0 == r1:
            return self.lines[r0][c0:c1]
        parts = [self.lines[r0][c0:]]
        parts.extend(self.lines[r0 + 1 : r1])
        parts.append(self.lines[r1][:c1])
        return "\n".join(parts)

    def delete_selection(self, *, record: bool = True, kind: str = "delete") -> bool:
        rng = self.selection_range()
        if rng is None:
            return False
        if record:
            self._record(kind)
        r0, c0, r1, c1 = rng
        before = self.lines[r0][:c0]
        after = self.lines[r1][c1:]
        self.lines[r0] = before + after
        del self.lines[r0 + 1 : r1 + 1]
        self.row, self.col = r0, c0
        self.clear_selection()
        self._mark_dirty()
        return True

    def select_word_at_cursor(self) -> None:
        line = self.lines[self.row]
        a, b = _word_bounds(line, self.col)
        if a == b:
            self.clear_selection()
            return
        self.sel_anchor = (self.row, a)
        self.col = b

    # --- caret / scroll ----------------------------------------------------

    def ensure_cursor_visible(
        self, line_h: int, view_h: int, font: Any | None = None, view_w: int = 0
    ) -> None:
        """Keep caret inside the padded text viewport (vertical + optional horizontal)."""
        y = self.row * line_h
        if y < self.scroll_y:
            self.scroll_y = max(0, y)
        elif y + line_h > self.scroll_y + view_h:
            self.scroll_y = max(0, y + line_h - view_h)

        if font is not None and view_w > 0:
            prefix = self.lines[self.row][: self.col]
            cx = font.size(prefix)[0]
            caret_pad = max(6, font.size("M")[0])
            if cx < self.scroll_x:
                self.scroll_x = max(0, cx - caret_pad)
            elif cx + caret_pad > self.scroll_x + view_w:
                self.scroll_x = max(0, cx + caret_pad - view_w)

    def pos_at(
        self,
        local_x: int,
        local_y: int,
        font: Any,
        line_h: int,
        panel_pad: int,
    ) -> tuple[int, int]:
        """Map panel-local pixel to (row, col)."""
        row = (local_y + self.scroll_y - panel_pad) // max(1, line_h)
        row = max(0, min(int(row), len(self.lines) - 1))
        line = self.lines[row]
        col = 0
        x = panel_pad - self.scroll_x
        target = local_x
        while col < len(line):
            w = font.size(line[col])[0]
            if x + w / 2.0 >= target:
                break
            x += w
            col += 1
        return row, col

    def word_at(
        self,
        local_x: int,
        local_y: int,
        font: Any,
        line_h: int,
        panel_pad: int,
    ) -> tuple[str, int, int] | None:
        """Return ``(word, row, col_start)`` under panel-local coords, or None."""
        row, col = self.pos_at(local_x, local_y, font, line_h, panel_pad)
        if row < 0 or row >= len(self.lines):
            return None
        line = self.lines[row]
        a, b = _word_bounds(line, col)
        if a >= b:
            return None
        return line[a:b], row, a

    def click_at(
        self,
        local_x: int,
        local_y: int,
        font: Any,
        line_h: int,
        view_h: int,
        view_w: int = 0,
        *,
        panel_pad: int = 10,
        extend: bool = False,
        double: bool = False,
    ) -> None:
        self.focused = True
        row, col = self.pos_at(local_x, local_y, font, line_h, panel_pad)
        if double:
            self.row, self.col = row, col
            self.select_word_at_cursor()
            self._selecting = False
        elif extend and self.sel_anchor is not None:
            self.row, self.col = row, col
            self._selecting = True
        else:
            self.row, self.col = row, col
            self.sel_anchor = (row, col)
            self._selecting = True
            # Click without drag → no selection until drag moves caret.
        self.ensure_cursor_visible(line_h, view_h, font, view_w)

    def drag_to(
        self,
        local_x: int,
        local_y: int,
        font: Any,
        line_h: int,
        view_h: int,
        view_w: int = 0,
        *,
        panel_pad: int = 10,
    ) -> None:
        if not self._selecting:
            return
        if self.sel_anchor is None:
            self.sel_anchor = (self.row, self.col)
        self.row, self.col = self.pos_at(local_x, local_y, font, line_h, panel_pad)
        self.ensure_cursor_visible(line_h, view_h, font, view_w)

    def end_mouse_select(self) -> None:
        self._selecting = False
        if self.sel_anchor is not None and self.sel_anchor == (self.row, self.col):
            self.clear_selection()

    # --- edits -------------------------------------------------------------

    def insert_text(self, text: str, *, kind: str = "insert") -> None:
        if not text:
            return
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
        if self.has_selection():
            # Replacement is one undo step (not coalesced with prior inserts).
            self._record("replace")
            self.delete_selection(record=False)
            kind = "replace"  # already recorded
            recorded = True
        else:
            recorded = False
        if not recorded:
            self._record(kind if kind != "replace" else "insert")
        parts = text.split("\n")
        line = self.lines[self.row]
        before, after = line[: self.col], line[self.col :]
        if len(parts) == 1:
            self.lines[self.row] = before + parts[0] + after
            self.col = len(before) + len(parts[0])
        else:
            self.lines[self.row] = before + parts[0]
            mid = parts[1:-1]
            self.lines[self.row + 1 : self.row + 1] = mid
            insert_at = self.row + 1 + len(mid)
            self.lines.insert(insert_at, parts[-1] + after)
            self.row = insert_at
            self.col = len(parts[-1])
        self.clear_selection()
        self._mark_dirty()

    def undo(self) -> bool:
        snap = self.history.undo(self.snapshot())
        if snap is None:
            return False
        self.restore(snap)
        return True

    def redo(self) -> bool:
        snap = self.history.redo(self.snapshot())
        if snap is None:
            return False
        self.restore(snap)
        return True

    def _move_left(self) -> None:
        if self.col > 0:
            self.col -= 1
        elif self.row > 0:
            self.row -= 1
            self.col = len(self.lines[self.row])

    def _move_right(self) -> None:
        if self.col < len(self.lines[self.row]):
            self.col += 1
        elif self.row + 1 < len(self.lines):
            self.row += 1
            self.col = 0

    def _move_up(self) -> None:
        if self.row > 0:
            self.row -= 1
            self.col = min(self.col, len(self.lines[self.row]))

    def _move_down(self) -> None:
        if self.row + 1 < len(self.lines):
            self.row += 1
            self.col = min(self.col, len(self.lines[self.row]))

    def handle_key(self, event: Any, pygame: Any) -> bool:
        """Handle KEYDOWN while focused. Returns True if consumed."""
        if not self.focused:
            return False
        mods = event.mod
        ctrl = bool(mods & (pygame.KMOD_CTRL | pygame.KMOD_META))
        shift = bool(mods & pygame.KMOD_SHIFT)
        key = event.key

        # Let global shortcuts through when Ctrl is held (except editor ones).
        if ctrl and key in (pygame.K_s, pygame.K_RETURN, pygame.K_KP_ENTER):
            return False
        # Let global shortcuts through (Esc / fullscreen keys).
        if key in (pygame.K_ESCAPE, pygame.K_F11):
            return False
        if key == getattr(pygame, "K_F10", None):
            return False

        # Undo / redo
        if ctrl and key == pygame.K_z and not shift:
            return self.undo()
        if ctrl and (key == pygame.K_y or (key == pygame.K_z and shift)):
            return self.redo()

        # Clipboard
        if ctrl and key == pygame.K_c:
            if self.has_selection():
                clipboard_set(self.get_selected_text(), pygame)
            return True
        if ctrl and key == pygame.K_x:
            if self.has_selection():
                clipboard_set(self.get_selected_text(), pygame)
                self.delete_selection(kind="cut")
            return True
        if ctrl and key == pygame.K_v:
            clip = clipboard_get(pygame)
            if clip:
                self.insert_text(clip, kind="paste")
            return True
        if ctrl and key == pygame.K_a:
            self.sel_anchor = (0, 0)
            self.row = len(self.lines) - 1
            self.col = len(self.lines[self.row])
            return True

        if key == pygame.K_BACKSPACE:
            if self.has_selection():
                self.delete_selection(kind="delete")
            elif self.col > 0:
                self._record("delete")
                line = self.lines[self.row]
                self.lines[self.row] = line[: self.col - 1] + line[self.col :]
                self.col -= 1
                self._mark_dirty()
            elif self.row > 0:
                self._record("delete")
                prev = self.lines[self.row - 1]
                self.col = len(prev)
                self.lines[self.row - 1] = prev + self.lines[self.row]
                del self.lines[self.row]
                self.row -= 1
                self._mark_dirty()
            return True

        if key == pygame.K_DELETE:
            if self.has_selection():
                self.delete_selection(kind="delete")
            else:
                line = self.lines[self.row]
                if self.col < len(line):
                    self._record("delete")
                    self.lines[self.row] = line[: self.col] + line[self.col + 1 :]
                    self._mark_dirty()
                elif self.row + 1 < len(self.lines):
                    self._record("delete")
                    self.lines[self.row] = line + self.lines[self.row + 1]
                    del self.lines[self.row + 1]
                    self._mark_dirty()
            return True

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.has_selection():
                self.delete_selection(kind="delete")
            self._record("newline")
            line = self.lines[self.row]
            self.lines[self.row] = line[: self.col]
            self.lines.insert(self.row + 1, line[self.col :])
            self.row += 1
            self.col = 0
            self.clear_selection()
            self._mark_dirty()
            return True

        if key == pygame.K_LEFT:
            if shift:
                if self.sel_anchor is None:
                    self.sel_anchor = (self.row, self.col)
                self._move_left()
            elif self.has_selection():
                rng = self.selection_range()
                assert rng is not None
                self.row, self.col = rng[0], rng[1]
                self.clear_selection()
            else:
                self.clear_selection()
                self._move_left()
            return True

        if key == pygame.K_RIGHT:
            if shift:
                if self.sel_anchor is None:
                    self.sel_anchor = (self.row, self.col)
                self._move_right()
            elif self.has_selection():
                rng = self.selection_range()
                assert rng is not None
                self.row, self.col = rng[2], rng[3]
                self.clear_selection()
            else:
                self.clear_selection()
                self._move_right()
            return True

        if key == pygame.K_UP:
            if shift:
                if self.sel_anchor is None:
                    self.sel_anchor = (self.row, self.col)
                self._move_up()
            else:
                self.clear_selection()
                self._move_up()
            return True

        if key == pygame.K_DOWN:
            if shift:
                if self.sel_anchor is None:
                    self.sel_anchor = (self.row, self.col)
                self._move_down()
            else:
                self.clear_selection()
                self._move_down()
            return True

        if key == pygame.K_HOME:
            if shift:
                if self.sel_anchor is None:
                    self.sel_anchor = (self.row, self.col)
            else:
                self.clear_selection()
            self.col = 0
            return True

        if key == pygame.K_END:
            if shift:
                if self.sel_anchor is None:
                    self.sel_anchor = (self.row, self.col)
            else:
                self.clear_selection()
            self.col = len(self.lines[self.row])
            return True

        if key == pygame.K_TAB:
            self.insert_text("    ", kind="insert")
            return True

        # Prefer KEYDOWN.unicode for ASCII editing (TEXTINPUT can double-fire).
        if not ctrl and event.unicode and event.unicode.isprintable():
            self.insert_text(event.unicode, kind="insert")
            return True

        return False

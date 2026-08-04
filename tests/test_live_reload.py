"""Live hot-reload: recompile from disk twice and render without reflection errors."""



from __future__ import annotations



from pathlib import Path



import numpy as np



from slang_falcon.device import clear_caches, clear_module_cache, load_module_from_path
from slang_falcon import ASSETS_DIR, SLANG_DIR
from slang_falcon.live import (
    CodeEditor,
    hotswap_temp_path,
    load_shader,
    render_frame,
    run_once,
)





def test_reload_twice_renders(tmp_path: Path):

    clear_caches()

    src_path = Path(__file__).resolve().parents[1] / "slang" / "lab_kernels.slang"

    text = src_path.read_text(encoding="utf-8")

    shader = tmp_path / "lab_kernels.slang"

    shader.write_text(text, encoding="utf-8")



    m1 = load_shader(shader)

    img1 = render_frame(m1, "hello_pixel", 32, 32)

    assert img1.shape == (32, 32, 3)

    z1 = float(img1[0, 0, 2])

    assert abs(z1 - 0.25) < 1e-5



    shader.write_text(text.replace("0.25f", "0.7f"), encoding="utf-8")

    m1 = None  # drop old generation

    m2 = load_shader(shader)

    img2 = render_frame(m2, "hello_pixel", 32, 32)

    assert abs(float(img2[0, 0, 2]) - 0.7) < 1e-5



    # Second frame on the same generation must not invalidate reflection

    img3 = render_frame(m2, "hello_pixel", 32, 32)

    assert abs(float(img3[0, 0, 2]) - 0.7) < 1e-5



    # Third generation

    shader.write_text(text.replace("0.25f", "0.15f"), encoding="utf-8")

    m3 = load_shader(shader)

    img4 = render_frame(m3, "hello_pixel", 16, 16)

    assert abs(float(img4[0, 0, 2]) - 0.15) < 1e-5

    np.testing.assert_allclose(img4[..., 2], 0.15, atol=1e-5)





def test_once_still_works(tmp_path: Path):

    clear_caches()

    out = tmp_path / "hello.png"

    src = Path(__file__).resolve().parents[1] / "slang" / "lab_kernels.slang"

    img = run_once(src, "hello_pixel", 64, 64, out=out)

    assert out.exists()

    assert img.shape == (64, 64, 3)


def test_code_editor_line_buffer():
    ed = CodeEditor()
    ed.set_text("alpha\nbeta", dirty=False)
    assert ed.lines == ["alpha", "beta"]
    assert not ed.dirty

    ed.row, ed.col = 0, 5
    ed.insert_text("\ngamma")
    assert ed.lines == ["alpha", "gamma", "beta"]
    assert ed.dirty
    assert ed.get_text() == "alpha\ngamma\nbeta"

    # Backspace merges lines
    class _Ev:
        def __init__(self, key, unicode="", mod=0):
            self.key = key
            self.unicode = unicode
            self.mod = mod

    class _Pg:
        KMOD_CTRL = 64
        KMOD_META = 128
        KMOD_SHIFT = 1
        K_BACKSPACE = 8
        K_DELETE = 127
        K_RETURN = 13
        K_KP_ENTER = 271
        K_LEFT = 276
        K_RIGHT = 275
        K_UP = 273
        K_DOWN = 274
        K_HOME = 278
        K_END = 279
        K_TAB = 9
        K_ESCAPE = 27
        K_F11 = 292
        K_s = 115
        K_z = 122
        K_y = 121
        K_c = 99
        K_x = 120
        K_v = 118
        K_a = 97

    ed.row, ed.col = 1, 0
    assert ed.handle_key(_Ev(_Pg.K_BACKSPACE), _Pg)
    assert ed.lines == ["alphagamma", "beta"]
    assert ed.row == 0 and ed.col == 5


def test_editor_undo_coalesce_and_redo():
    from slang_falcon.code_editor import EditorHistory

    clock = {"t": 0.0}

    def now() -> float:
        return clock["t"]

    hist = EditorHistory(max_depth=100, coalesce_s=0.4, clock=now)
    ed = CodeEditor(history=hist)
    ed.set_text("hi", dirty=False)
    ed.row, ed.col = 0, 2

    # Rapid inserts coalesce into one undo chunk.
    ed.insert_text("a", kind="insert")
    clock["t"] = 0.1
    ed.insert_text("b", kind="insert")
    clock["t"] = 0.2
    ed.insert_text("c", kind="insert")
    assert ed.get_text() == "hiabc"
    assert len(hist._undo) == 1

    assert ed.undo()
    assert ed.get_text() == "hi"
    assert not ed.dirty

    assert ed.redo()
    assert ed.get_text() == "hiabc"
    assert ed.dirty

    # Pause then type → new chunk; delete breaks insert coalesce.
    clock["t"] = 1.0
    ed.row, ed.col = 0, len(ed.lines[0])
    ed.insert_text("x", kind="insert")
    clock["t"] = 1.05
    ed.insert_text("y", kind="insert")
    assert len(hist._undo) == 2
    clock["t"] = 2.0
    ed.row, ed.col = 0, len(ed.lines[0])
    class _Ev:
        def __init__(self, key, unicode="", mod=0):
            self.key = key
            self.unicode = unicode
            self.mod = mod

    class _Pg:
        KMOD_CTRL = 64
        KMOD_META = 128
        KMOD_SHIFT = 1
        K_BACKSPACE = 8
        K_DELETE = 127
        K_RETURN = 13
        K_KP_ENTER = 271
        K_LEFT = 276
        K_RIGHT = 275
        K_UP = 273
        K_DOWN = 274
        K_HOME = 278
        K_END = 279
        K_TAB = 9
        K_ESCAPE = 27
        K_F11 = 292
        K_s = 115
        K_z = 122
        K_y = 121
        K_c = 99
        K_x = 120
        K_v = 118
        K_a = 97

    ed.handle_key(_Ev(_Pg.K_BACKSPACE), _Pg)
    assert ed.get_text() == "hiabcx"
    assert len(hist._undo) == 3
    ed.undo()
    assert ed.get_text() == "hiabcxy"


def test_editor_selection_replace_and_delete():
    ed = CodeEditor()
    ed.set_text("one two three", dirty=False)
    ed.sel_anchor = (0, 4)
    ed.row, ed.col = 0, 7  # select "two"
    assert ed.get_selected_text() == "two"
    ed.insert_text("2")
    assert ed.get_text() == "one 2 three"
    assert not ed.has_selection()
    assert ed.dirty

    ed.sel_anchor = (0, 0)
    ed.row, ed.col = 0, 3
    assert ed.delete_selection()
    assert ed.get_text() == " 2 three"
    ed.undo()
    assert ed.get_text() == "one 2 three"


def test_hotswap_temp_path_under_cache():
    shader = SLANG_DIR / "lab_kernels.slang"
    path = hotswap_temp_path(shader)
    assert path.name == "live_hotswap_lab_kernels.slang"
    assert path.parent == (ASSETS_DIR / "cache").resolve()


def test_hotswap_compile_does_not_touch_real(tmp_path: Path):
    """Editor buffer → temp file compile; real shader mtime unchanged."""
    clear_caches()
    src = Path(__file__).resolve().parents[1] / "slang" / "lab_kernels.slang"
    original = src.read_text(encoding="utf-8")
    real_mtime = src.stat().st_mtime

    hot = tmp_path / "live_hotswap_lab_kernels.slang"
    edited = original.replace("0.25f", "0.55f")
    hot.write_text(edited, encoding="utf-8")

    clear_module_cache()
    module = load_module_from_path(
        hot, search_paths=[SLANG_DIR, src.parent], fresh=True
    )
    img = render_frame(module, "hello_pixel", 16, 16)
    assert abs(float(img[0, 0, 2]) - 0.55) < 1e-5

    assert src.read_text(encoding="utf-8") == original
    assert abs(src.stat().st_mtime - real_mtime) < 1e-6



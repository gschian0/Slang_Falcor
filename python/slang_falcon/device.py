"""Device / module helpers for SlangPy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from slang_falcon import SLANG_DIR

_device = None
_modules: dict[str, Any] = {}
_reload_generation = 0


def get_device():
    """Create (or reuse) a SlangPy device.

    Tries D3D12, then Vulkan, Metal, CUDA. Hot-reload is disabled: slangpy's
    file watcher can invalidate reflection mid-frame; live.py recompiles by
    loading source with a fresh module name instead.
    """
    global _device
    if _device is not None:
        return _device

    import slangpy as spy

    last_err: Exception | None = None
    for type_name in ("d3d12", "vulkan", "metal", "cuda"):
        try:
            device_type = getattr(spy.DeviceType, type_name)
            _device = spy.create_device(device_type, enable_hot_reload=False)
            return _device
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    try:
        _device = spy.create_device(enable_hot_reload=False)
        return _device
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Failed to create a SlangPy device. Install GPU drivers and slangpy."
        ) from (last_err or exc)


def _include_paths(search_paths: list[Path] | None, slang_file: Path) -> list[str]:
    raw_dirs = [str(p.resolve()) for p in (search_paths or [SLANG_DIR, slang_file.parent])]
    include_dirs: list[str] = []
    for d in raw_dirs:
        if d not in include_dirs:
            include_dirs.append(d)
    return include_dirs


def load_module(
    name: str,
    search_paths: list[Path] | None = None,
    *,
    force: bool = False,
):
    """Load a .slang file from slang/ (cached). Pass force=True to recompile."""
    if force:
        _modules.pop(name, None)
    elif name in _modules:
        return _modules[name]

    slang_file = SLANG_DIR / f"{name}.slang"
    if not slang_file.exists():
        raise FileNotFoundError(slang_file)

    module = load_module_from_path(slang_file, search_paths=search_paths)
    _modules[name] = module
    return module


def load_module_from_path(
    slang_file: Path,
    search_paths: list[Path] | None = None,
    *,
    fresh: bool = False,
):
    """Load a .slang module from an arbitrary path.

    With fresh=False (default), uses slangpy load_from_file (session-cached).
    With fresh=True, reads source and load_from_source under a unique name so
    edits on disk are recompiled — required for live hot-reload.
    """
    import slangpy as spy

    slang_file = Path(slang_file).resolve()
    if not slang_file.exists():
        raise FileNotFoundError(slang_file)

    device = get_device()
    include_dirs = _include_paths(search_paths, slang_file)
    options: dict[str, Any] = {"include_paths": include_dirs}

    if fresh:
        global _reload_generation
        _reload_generation += 1
        source = slang_file.read_text(encoding="utf-8")
        # Unique session name — source may still declare `module lab_kernels;`
        module_name = f"{slang_file.stem}__live_{_reload_generation}"
        try:
            return spy.Module.load_from_source(
                device, module_name, source, options=options
            )
        except TypeError:
            return spy.Module.load_from_source(device, module_name, source)

    try:
        return spy.Module.load_from_file(
            device, str(slang_file), options=options
        )
    except TypeError:
        return spy.Module.load_from_file(device, str(slang_file))


def clear_module_cache() -> None:
    """Drop cached modules (keeps the device). Useful for live reload."""
    global _modules
    _modules = {}


def clear_caches() -> None:
    global _device, _modules, _reload_generation
    _device = None
    _modules = {}
    _reload_generation = 0

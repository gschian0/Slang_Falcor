"""Load and resolve the live lesson curriculum (labs/curriculum.json)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from slang_falcon import REPO_ROOT

CURRICULUM_PATH = REPO_ROOT / "labs" / "curriculum.json"


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str
    shader: Path
    entry: str
    markdown: Path
    blurb: str
    phase_id: str
    phase_title: str
    index: int  # global 0-based index across all phases
    interactive_mouse: bool = False  # primary-drag updates shader mouse, not window
    texture: Path | None = None  # optional Texture2D asset for live binding


def _resolve_repo_path(rel: str) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p.resolve()
    return (REPO_ROOT / p).resolve()


def load_curriculum(path: Path | None = None) -> list[Lesson]:
    """Return ordered lessons from curriculum.json."""
    path = path or CURRICULUM_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    lessons: list[Lesson] = []
    idx = 0
    for phase in data.get("phases", []):
        phase_id = str(phase.get("id", ""))
        phase_title = str(phase.get("title", phase_id))
        for raw in phase.get("lessons", []):
            tex_raw = raw.get("texture")
            texture = _resolve_repo_path(str(tex_raw)) if tex_raw else None
            lessons.append(
                Lesson(
                    id=str(raw["id"]),
                    title=str(raw["title"]),
                    shader=_resolve_repo_path(str(raw["shader"])),
                    entry=str(raw.get("entry", "hello_pixel")),
                    markdown=_resolve_repo_path(str(raw["markdown"])),
                    blurb=str(raw.get("blurb", "")),
                    phase_id=phase_id,
                    phase_title=phase_title,
                    index=idx,
                    interactive_mouse=bool(raw.get("interactive_mouse", False)),
                    texture=texture,
                )
            )
            idx += 1
    return lessons


def curriculum_meta(path: Path | None = None) -> dict:
    path = path or CURRICULUM_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def find_lesson(spec: str | int, lessons: list[Lesson] | None = None) -> Lesson:
    """Resolve ``--lesson``: int index, full id, or short suffix (e.g. ``00_hello``)."""
    lessons = lessons if lessons is not None else load_curriculum()
    if not lessons:
        raise SystemExit(f"No lessons in {CURRICULUM_PATH}")

    if isinstance(spec, int) or (isinstance(spec, str) and spec.isdigit()):
        i = int(spec)
        if i < 0 or i >= len(lessons):
            raise SystemExit(f"Lesson index {i} out of range 0..{len(lessons) - 1}")
        return lessons[i]

    key = str(spec).strip().replace("\\", "/")
    # Exact id
    for les in lessons:
        if les.id == key:
            return les
    # Suffix / stem match (bos/00_hello, 00_hello, neural/n01_…)
    for les in lessons:
        if les.id.endswith("/" + key) or les.id.split("/")[-1] == key:
            return les
    # Shader stem
    for les in lessons:
        if les.shader.stem == key or key in les.shader.as_posix():
            return les

    ids = ", ".join(les.id for les in lessons)
    raise SystemExit(f"Unknown lesson {spec!r}. Known ids: {ids}")


def format_lesson_list(lessons: list[Lesson] | None = None) -> str:
    lessons = lessons if lessons is not None else load_curriculum()
    lines: list[str] = []
    cur_phase = None
    for les in lessons:
        if les.phase_id != cur_phase:
            cur_phase = les.phase_id
            lines.append(f"\n[{les.phase_id}] {les.phase_title}")
        lines.append(f"  {les.index:2d}  {les.id:<32}  {les.title}")
        if les.blurb:
            lines.append(f"      {les.blurb}")
    return "\n".join(lines).lstrip("\n")


def lesson_banner_lines(les: Lesson, *, max_try: int = 2) -> list[str]:
    """Short on-screen explanation: title, blurb, optional Try bullets from markdown."""
    n_total_hint = ""
    lines = [
        f"Lesson {les.index} - {les.title}  [{les.phase_id}]",
    ]
    if les.blurb:
        lines.append(les.blurb)
    try_bits: list[str] = []
    if les.markdown.exists():
        try:
            raw = les.markdown.read_text(encoding="utf-8")
        except OSError:
            raw = ""
        in_try = False
        for line in raw.splitlines():
            s = line.strip()
            if s.startswith("## ") and "try" in s.lower():
                in_try = True
                continue
            if in_try and s.startswith("## "):
                break
            if in_try and s.startswith(("1.", "2.", "3.", "4.", "5.", "-", "*")):
                tip = s.lstrip("0123456789.-* ").strip()
                # Drop markdown links / backticks for the on-screen strip.
                while "[" in tip and "](" in tip:
                    a = tip.find("[")
                    b = tip.find("](", a)
                    c = tip.find(")", b)
                    if a < 0 or b < 0 or c < 0:
                        break
                    tip = tip[:a] + tip[a + 1 : b] + tip[c + 1 :]
                tip = tip.replace("`", "")
                if tip:
                    try_bits.append(tip)
                if len(try_bits) >= max_try:
                    break
    for tip in try_bits:
        lines.append(f"Try: {tip}")
    if n_total_hint:
        lines[0] = f"{lines[0]}{n_total_hint}"
    return lines

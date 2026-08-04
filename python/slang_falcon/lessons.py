"""Print the live curriculum and how to run lessons.

Usage:
    python -m slang_falcon.lessons
    python -m slang_falcon.lessons --json
"""

from __future__ import annotations

import argparse
import json

from slang_falcon.curriculum import (
    CURRICULUM_PATH,
    curriculum_meta,
    format_lesson_list,
    load_curriculum,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="List VERNACULAR live curriculum lessons (package: slang_falcon)"
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Dump curriculum.json (resolved paths as relative)",
    )
    args = p.parse_args(argv)

    if args.json:
        print(json.dumps(curriculum_meta(), indent=2))
        return 0

    meta = curriculum_meta()
    lessons = load_curriculum()
    def out(s: str = "") -> None:
        # Windows consoles may be cp1252; avoid hard UnicodeEncodeError.
        try:
            print(s)
        except UnicodeEncodeError:
            print(s.encode("ascii", "replace").decode("ascii"))

    out(meta.get("title", "Curriculum"))
    if meta.get("blurb"):
        out(meta["blurb"])
    out(f"Source: {CURRICULUM_PATH}")
    out(f"Lessons: {len(lessons)}")
    out()
    out(format_lesson_list(lessons))
    out()
    out("Run:")
    out("  python -m slang_falcon.live --lesson 0")
    out("  python -m slang_falcon.live --lesson bos/00_hello")
    out("  python -m slang_falcon.live --lesson slang_playground/sp01_simple_image")
    out("  python -m slang_falcon.live --lesson diffslang/d01_differentiable_attr")
    out("  python -m slang_falcon.live --lesson neural_shading/ns01_trainable_pipeline")
    out("  python -m slang_falcon.live --lesson neural_gfx_afternoon/ng01_slangpy_calls")
    out("  # Trilogy hub: labs/neural_trilogy/README.md")
    out()
    out("In the live window (editor unfocused):")
    out("  [ or Left   previous lesson")
    out("  ] or Right  next lesson")
    out("  L           print lesson list in console")
    out("  0-9         jump to lesson index (optional)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

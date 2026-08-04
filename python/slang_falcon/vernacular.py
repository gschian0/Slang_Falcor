"""VERNACULAR product face — thin alias for the live playground.

Usage:
    python -m slang_falcon.vernacular --lesson 0
    vernacular --lesson 0   # after ``pip install -e .``
"""

from __future__ import annotations

from slang_falcon.live import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())

"""Small helpers for MathMongo-style HTML controls."""

from __future__ import annotations

import re


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return re.sub(r"_+", "_", slug).lower() or "graph"

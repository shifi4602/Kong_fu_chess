"""Pure straight-line interpolation between two points. No engine
coupling, no coordinate-system knowledge -- just lerp. Motion.progress()
already accounts for the whole src->dst travel time, so this deliberately
lerps straight from src to dst rather than stepping through intermediate
path cells.
"""
from __future__ import annotations

from typing import Tuple


def lerp_point(src: Tuple[float, float], dst: Tuple[float, float], progress: float) -> Tuple[float, float]:
    src_x, src_y = src
    dst_x, dst_y = dst
    return src_x + (dst_x - src_x) * progress, src_y + (dst_y - src_y) * progress

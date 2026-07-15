from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Tuple

from ui.rendering.canvas import Canvas, ImageHandle

from .asset_paths import config_path, sprites_dir


@dataclass(frozen=True)
class StateConfig:
    frames_per_sec: float
    is_loop: bool
    next_state_when_finished: str


@dataclass(frozen=True)
class StateSprites:
    config: StateConfig
    frames: Tuple[ImageHandle, ...]


class SpriteLoader:
    """Loads and caches, per (piece code, state), the animation config and
    every frame image under ui/assets/pieces_mine. Depends on `Canvas`
    only through `load_image` -- it never touches cv2/Img directly.
    """

    def __init__(self, canvas: Canvas, cell_size: int) -> None:
        self._canvas = canvas
        self._cell_size = cell_size
        self._cache: Dict[Tuple[str, str], StateSprites] = {}

    def load(self, code: str, state: str) -> StateSprites:
        key = (code, state)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        loaded = StateSprites(
            config=self._load_config(code, state),
            frames=self._load_frames(code, state),
        )
        self._cache[key] = loaded
        return loaded

    def _load_config(self, code: str, state: str) -> StateConfig:
        with open(config_path(code, state), "r", encoding="utf-8") as f:
            raw = json.load(f)
        return StateConfig(
            frames_per_sec=raw["graphics"]["frames_per_sec"],
            is_loop=raw["graphics"]["is_loop"],
            next_state_when_finished=raw["physics"]["next_state_when_finished"],
        )

    def _load_frames(self, code: str, state: str) -> Tuple[ImageHandle, ...]:
        paths = sorted(sprites_dir(code, state).glob("*.png"), key=lambda p: int(p.stem))
        return tuple(
            self._canvas.load_image(p, size=(self._cell_size, self._cell_size), keep_aspect=True)
            for p in paths
        )

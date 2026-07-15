from __future__ import annotations

from pathlib import Path

ASSETS_ROOT = Path(__file__).resolve().parent
PIECES_ROOT = ASSETS_ROOT / "pieces_mine"
BOARD_IMAGE = ASSETS_ROOT / "board.png"


def state_dir(code: str, state: str) -> Path:
    return PIECES_ROOT / code / "states" / state


def config_path(code: str, state: str) -> Path:
    return state_dir(code, state) / "config.json"


def sprites_dir(code: str, state: str) -> Path:
    return state_dir(code, state) / "sprites"

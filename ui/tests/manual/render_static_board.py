"""Manual verification tool, not a pytest test (pytest only collects
`test_*`): renders the standard starting position's board + idle sprites
through the real `ui/platform` Canvas and saves a PNG, so the pipeline can
be inspected without a live window.

Run: python -m ui.tests.manual.render_static_board [output.png]
"""
from __future__ import annotations

import sys
from pathlib import Path

import kungfu_chess.config as config
from kungfu_chess.input import BoardMapper
from ui.animation import SceneBuilder
from ui.assets import SpriteLoader
from ui.assets.asset_paths import BOARD_IMAGE
from ui.main import build_engine
from ui.platform import OffscreenImgCanvas
from ui.rendering import BoardRenderer, CoordinateMapper


def render(output_path: Path) -> None:
    engine = build_engine()
    board = engine.get_snapshot().board

    canvas = OffscreenImgCanvas()
    width = config.CELL_SIZE * config.BOARD_COLS
    height = config.CELL_SIZE * config.BOARD_ROWS
    background = canvas.load_image(BOARD_IMAGE, size=(width, height))

    mapper = CoordinateMapper(
        BoardMapper(cell_size=config.CELL_SIZE, rows=board.rows, cols=board.cols),
        config.CELL_SIZE,
    )
    loader = SpriteLoader(canvas, config.CELL_SIZE)
    renderer = BoardRenderer(canvas, background)
    scene = SceneBuilder(canvas, mapper, loader)

    snapshot = engine.get_snapshot()
    placements = scene.build(snapshot, render_now=0.0)

    renderer.render(placements)
    canvas.save(output_path)


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("board_proof.png")
    render(output)
    print(f"wrote {output}")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

collect_ignore = [
    "tests/test_chess_engine.py",
    "tests/test_main_pipeline.py",
    "tests/test_movement_strategies.py",
    "tests/test_types_and_constants.py",
]

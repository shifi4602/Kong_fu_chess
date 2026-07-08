import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

engine_path = ROOT / "chess engine"
parser_path = ROOT / "print the board"

for path in [engine_path, parser_path]:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
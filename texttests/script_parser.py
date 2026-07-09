from dataclasses import dataclass, field
from typing import List

_COMMAND_KEYWORDS = frozenset({
    'BOARD', 'CLICK', 'TICK',
    'ASSERT_CELL', 'ASSERT_WINNER', 'ASSERT_GAME_OVER', 'ASSERT_ALIVE',
})


@dataclass
class ScriptCommand:
    kind: str
    args: list = field(default_factory=list)


class ScriptParser:
    def parse(self, text: str) -> List[ScriptCommand]:
        commands: List[ScriptCommand] = []
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            if not line:
                continue
            if line.startswith('#'):
                continue
            parts = line.split()
            keyword = parts[0].upper()
            if keyword not in _COMMAND_KEYWORDS:
                continue
            if keyword == 'BOARD':
                board_lines: List[str] = []
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line:
                        i += 1
                        continue
                    if next_line.startswith('#'):
                        i += 1
                        continue
                    next_parts = next_line.split()
                    if next_parts[0].upper() in _COMMAND_KEYWORDS:
                        break
                    board_lines.append(next_line)
                    i += 1
                board_text = '\n'.join(board_lines)
                commands.append(ScriptCommand(kind='BOARD', args=[board_text]))
            else:
                commands.append(ScriptCommand(kind=keyword, args=parts[1:]))
        return commands

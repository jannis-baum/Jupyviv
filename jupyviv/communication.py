import sys
from typing import Callable

type Handler = Callable[[list[str]], None]

class JupyVivError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

def _output(i: int, message: str, is_error: bool = False):
    print(f'[{i}]: {"ERROR: " if is_error else ""}{message}')
    sys.stdout.flush()

def _error(i: int, message: str):
    _output(i, message, is_error=True)

def run(handlers: dict[str, Handler]):
    for i, line in enumerate(sys.stdin):
        try:
            args = line.split()
            if len(args) == 0:
                continue

            command = args[0]
            if command not in handlers:
                _error(i, f'Unknown command: {command}')
                continue

            handlers[command](args[1:])
            _output(i, 'Done')
        except JupyVivError as e:
            _error(i, str(e))

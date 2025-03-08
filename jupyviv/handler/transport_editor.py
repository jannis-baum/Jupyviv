import sys
from typing import Callable

from jupyviv.shared.logs import get_logger
from jupyviv.shared.error import JupyVivError

type Handler = Callable[[list[str]], str | None]

_logger = get_logger(__name__)

def _output(i: int, message: str, is_error: bool = False):
    print(f'[{i}]: {"ERROR: " if is_error else ""}{message}')
    sys.stdout.flush()

def _error(i: int, message: str):
    _output(i, message, is_error=True)

# interrupt mode flushes out any remaining input, e.g. when the kernel should
# be interrupted all additional commands are ignored
# returns (should_continue, last_line)
def _interrupt_mode(start_line: int) -> tuple[bool, int]:
    i = start_line - 1
    try:
        for line in sys.stdin:
            i += 1
            if line.strip() == 'continue':
                return True, i
    except KeyboardInterrupt:
        return False, i
    return False, i

def run(handlers: dict[str, Handler], start_line: int = 1):
    i = start_line - 1
    try:
        for line in sys.stdin:
            i += 1
            try:
                args = line.split()
                if len(args) == 0:
                    continue

                command = args[0]
                if command not in handlers:
                    _error(i, f'Unknown command: {command}')
                    continue

                result = handlers[command](args[1:])
                _output(i, result if result else 'Done')
            except JupyVivError as e:
                _error(i, str(e))
    except KeyboardInterrupt:
        _logger.info('Entering interrupt mode, type "continue" to resume')
        should_continue, i = _interrupt_mode(i)
        if not should_continue:
            _logger.info('Interrupted again, exiting')
            return
        _logger.info('Exiting interrupt mode, resuming')
        return run(handlers, i)

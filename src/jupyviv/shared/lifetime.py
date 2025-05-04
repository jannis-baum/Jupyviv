import asyncio
import os
import signal
import sys

from jupyviv.shared.logs import get_logger

_logger = get_logger(__file__)

# monitor if parent process is still alive; if not, gracefully shut down
async def shutdown_with_parent(interval=1, shutdown_timeout=10):
    ppid = os.getppid()

    while True:
        if os.getppid() != ppid or ppid == 1:
            _logger.info('Parent process died, shutting down')
            os.kill(os.getpid(), signal.SIGINT)
            await asyncio.sleep(shutdown_timeout)
            _logger.warning('Failed to gracefully shut down without deadline, exiting')
            sys.exit(1)
        await asyncio.sleep(interval)

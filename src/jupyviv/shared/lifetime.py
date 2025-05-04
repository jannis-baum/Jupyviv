import asyncio
import os
import signal
import sys

from jupyviv.shared.logs import get_logger

_logger = get_logger(__file__)

async def shutdown(timeout=1):
    os.kill(os.getpid(), signal.SIGINT)
    await asyncio.sleep(timeout)
    _logger.warning('Failed to gracefully shut down without deadline, exiting')
    sys.exit(1)

# monitor if parent process is still alive; if not, gracefully shut down
async def shutdown_with_parent(interval=1, shutdown_timeout=1):
    ppid = os.getppid()

    while True:
        if os.getppid() != ppid or ppid == 1:
            _logger.info('Parent process died, shutting down')
            await shutdown(shutdown_timeout)
        await asyncio.sleep(interval)

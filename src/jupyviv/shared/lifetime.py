import asyncio
import os
import signal
import sys

import psutil

from jupyviv.shared.logs import get_logger

_logger = get_logger(__file__)

def _graceful_shutdown():
    os.kill(os.getpid(), signal.SIGINT)

# monitor if parent process is still alive; if not, gracefully shut down
async def shutdown_with_parent(interval=1, shutdown_timeout=10):
    ppid = os.getppid()
    try:
        parent = psutil.Process(ppid)
    except psutil.NoSuchProcess:
        _graceful_shutdown()
        return

    while True:
        if not parent.is_running() or parent.status() == psutil.STATUS_ZOMBIE:
            _logger.info('Parent process died, shutting down')
            os.kill(os.getpid(), signal.SIGINT)
            await asyncio.sleep(shutdown_timeout)
            _logger.warning('Failed to gracefully shut down without deadline, exiting')
            sys.exit(1)
        await asyncio.sleep(interval)

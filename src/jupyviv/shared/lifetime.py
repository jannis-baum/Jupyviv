import asyncio
import os
import signal
import sys

from jupyviv.shared.logs import get_logger

_logger = get_logger(__file__)


async def shutdown(timeout=1):
    # prevent anything else from being output (i.e. future errors are suppressed)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, 1)  # dup stdout to devnull
    os.dup2(devnull_fd, 2)  # dup stderr to devnull
    # try to shutdown gracefully with SIGINT
    os.kill(os.getpid(), signal.SIGINT)
    # wait and if we're still here, exit
    await asyncio.sleep(timeout)
    sys.exit(1)


# monitor if parent process is still alive; if not, gracefully shut down
async def shutdown_with_parent(interval=1, shutdown_timeout=1):
    ppid = os.getppid()

    while True:
        if os.getppid() != ppid or ppid == 1:
            _logger.info("Parent process died, shutting down")
            await shutdown(shutdown_timeout)
        await asyncio.sleep(interval)

import asyncio
import os
import signal

import psutil

def _graceful_shutdown():
    os.kill(os.getpid(), signal.SIGINT)

# monitor if parent process is still alive; if not, gracefully shut down
async def shutdown_with_parent(interval=1):
    ppid = os.getppid()
    try:
        parent = psutil.Process(ppid)
    except psutil.NoSuchProcess:
        _graceful_shutdown()
        return

    while True:
        if not parent.is_running() or parent.status() == psutil.STATUS_ZOMBIE:
            os.kill(os.getpid(), signal.SIGINT)
        await asyncio.sleep(interval)

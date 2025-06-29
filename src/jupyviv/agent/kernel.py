import asyncio
import json
import os
import time
from typing import Awaitable, Callable

from jupyter_client.asynchronous.client import AsyncKernelClient
from jupyter_client.ioloop.manager import AsyncIOLoopKernelManager
from jupyter_client.kernelspec import NoSuchKernel

from jupyviv.shared.errors import JupyvivError
from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import Message, MessageHandlerDict, MessageQueue
from jupyviv.shared.utils import dsafe

_logger = get_logger(__name__)
_output_msg_types = ["execute_result", "display_data", "stream", "error"]


# KernelManager.update_env doesn't work so we do this
def _setup_env():
    # set $TERM to support only 16 colors so it doesn't use explicit colors and
    # look horrible in dark mode
    os.environ["TERM"] = "xterm"
    # see https://github.com/plotly/plotly.py/blob/main/doc/python/renderers.md#setting-the-default-renderer
    os.environ["PLOTLY_RENDERER"] = "notebook_connected"


# adapted from `from jupyter_client.manager import start_new_async_kernel` but
# for AsyncIOLoopKernelManager because it monitors kernel crashes
async def _start_kernel(
    name: str, startup_timeout: float = 60
) -> tuple[AsyncIOLoopKernelManager, AsyncKernelClient]:
    try:
        km: AsyncIOLoopKernelManager = AsyncIOLoopKernelManager(kernel_name=name)
    except NoSuchKernel:
        raise JupyvivError(f'No such kernel "{name}"')

    await km.start_kernel()

    def _on_restart():
        _logger.warning("Kernel died, restarting")

    km.add_restart_callback(_on_restart)

    kc = km.client()
    kc.start_channels()
    try:
        await kc.wait_for_ready(timeout=startup_timeout)
    except Exception:
        kc.stop_channels()
        await km.shutdown_kernel()
        raise JupyvivError(f'Failed to launch kernel "{name}"')

    return (km, kc)


# returns message handler & runner for kernel
async def setup_kernel(
    name: str, send_queue: MessageQueue
) -> tuple[MessageHandlerDict, Callable[[], Awaitable[None]]]:
    _logger.info(f'Starting kernel "{name}"')
    _setup_env()
    km, kc = await _start_kernel(name)
    _logger.info("Kernel ready")

    id_kernel2jupyviv = dict[str, str]()

    async def _kernel_loop():
        try:
            while True:
                msg = await kc.get_iopub_msg()

                kernel_id = str(dsafe(msg, "parent_header", "msg_id"))
                jupyviv_id = id_kernel2jupyviv.get(kernel_id)
                if jupyviv_id is None:
                    continue

                msg_type = dsafe(msg, "msg_type")
                content = dsafe(msg, "content")

                if msg_type == "status":
                    # "busy" when starting to execute, "idle" when done
                    state = str(dsafe(content, "execution_state"))
                    send_queue.put(Message(jupyviv_id, "status", state))
                    continue

                if msg_type == "execute_input":
                    execution_count = str(dsafe(content, "execution_count"))
                    send_queue.put(
                        Message(jupyviv_id, "execute_input", execution_count)
                    )
                    continue

                if msg_type in _output_msg_types and type(content) is dict:
                    data = json.dumps({"output_type": msg_type, **content})
                    send_queue.put(Message(jupyviv_id, "output", data))
                    continue

                _logger.info(
                    f"Received unknown message: {msg_type} with content: {content}"
                )
        except asyncio.CancelledError:
            pass
        finally:
            kc.stop_channels()
            await km.shutdown_kernel()

    async def _execute(message: Message):
        kernel_id = kc.execute(message.args)
        id_kernel2jupyviv[kernel_id] = message.id

    async def _interrupt(_: Message):
        await km.interrupt_kernel()

    async def _restart(_: Message):
        await km.restart_kernel()

    async def _get_metadata(message: Message):
        async def _get_language_info():
            msg_id = kc.kernel_info()
            timeout = 3
            remaining = timeout
            start = time.monotonic()
            while remaining > 0:
                remaining = timeout - (time.monotonic() - start)
                try:
                    msg = await asyncio.wait_for(kc.get_shell_msg(), timeout=remaining)
                    if msg["parent_header"].get("msg_id") == msg_id:
                        return msg["content"]["language_info"]
                except asyncio.TimeoutError:
                    break
            return None

        language_info = await _get_language_info()
        name = km.kernel_name
        spec = km.kernel_spec
        if language_info is None or name is None or spec is None:
            send_queue.put(Message(message.id, "spec", "null"))
            return

        send_queue.put(
            Message(
                message.id,
                "metadata",
                json.dumps(
                    {
                        "kernelspec": {
                            "display_name": spec.display_name,
                            "language": spec.language,
                            "name": name,
                        },
                        "language_info": language_info,
                    }
                ),
            )
        )

    handlers = {
        "execute": _execute,
        "interrupt": _interrupt,
        "restart": _restart,
        "get_metadata": _get_metadata,
    }

    return (handlers, _kernel_loop)

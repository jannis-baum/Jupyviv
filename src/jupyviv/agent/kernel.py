import asyncio
import json
from typing import Awaitable, Callable

from jupyter_client.manager import start_new_async_kernel

from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import AsyncMessageHandler, AsyncMessageQueue, Message
from jupyviv.shared.utils import dsafe

_logger = get_logger(__name__)
_output_msg_types = ['execute_result', 'display_data', 'stream', 'error']

# returns message handler & runner for kernel
async def setup_kernel(name: str, send_queue: AsyncMessageQueue) -> tuple[AsyncMessageHandler, Callable[[], Awaitable[None]]]:
    _logger.info(f'Starting kernel {name}')
    km, kc = await start_new_async_kernel(kernel_name=name)
    _logger.info(f'Kernel ready')

    id_kernel2jupyviv = dict[str, str]()

    async def _kernel_loop():
        try:
            while True:
                msg = await kc.get_iopub_msg()

                kernel_id = str(dsafe(msg, 'parent_header', 'msg_id'))
                jupyviv_id = id_kernel2jupyviv.get(kernel_id)
                if jupyviv_id is None:
                    continue

                msg_type = dsafe(msg, 'msg_type')
                content = dsafe(msg, 'content')

                if msg_type == 'status':
                    state = str(dsafe(content, 'execution_state'))
                    await send_queue.put(Message(jupyviv_id, 'status', state))
                    continue

                if msg_type == 'execute_input':
                    execution_count = str(dsafe(content, 'execution_count'))
                    await send_queue.put(Message(jupyviv_id, 'execute_input', execution_count))
                    continue

                if msg_type in _output_msg_types and type(content) == dict:
                    data = json.dumps({ 'output_type': msg_type, **content })
                    await send_queue.put(Message(jupyviv_id, 'output', data))
                    continue

                _logger.info(f'Received unknown message: {msg_type} with content: {content}')
        finally:
            kc.stop_channels()
            await km.shutdown_kernel()

    async def _execute(message: Message):
        kernel_id = kc.execute(message.args)
        id_kernel2jupyviv[kernel_id] = message.id

    handler = AsyncMessageHandler({
        'execute': _execute
    })

    return (handler, _kernel_loop)

import asyncio
import json

from jupyviv.shared.errors import JupyVivError
from jupyviv.shared.messages import Message, MessageHandler, new_queue
from jupyviv.shared.transport.websocket import run_client

async def create_notebook(path: str, agent_addr: str):
    if not path.endswith('.ipynb'):
        raise JupyVivError('New Notebook needs to end in ".ipynb"')

    metadata_queue = asyncio.Queue()
    async def recv_metadata(message: Message):
        await metadata_queue.put(json.loads(message.args))

    send_queue = new_queue()
    await send_queue.put(Message('new', 'get_metadata'))
    handler = MessageHandler({ 'metadata': recv_metadata })

    async def run_communication():
        try:
            await run_client(agent_addr, handler, send_queue)
        except:
            pass
    socket_task = asyncio.create_task(run_communication())

    try:
        metadata = await asyncio.wait_for(metadata_queue.get(), timeout=10)
    except:
        raise JupyVivError('Failed to retrieve metadata from agent')
    finally:
        socket_task.cancel()
        await socket_task
    print(metadata)

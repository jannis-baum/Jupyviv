import asyncio
import json
import os
import subprocess

from jupyviv.shared.errors import JupyvivError
from jupyviv.shared.messages import Message, MessageHandler, new_queue
from jupyviv.shared.transport.websocket import run_client


async def create_notebook(path: str, agent_addr: str):
    if not path.endswith(".ipynb"):
        raise JupyvivError('New Notebook needs to end in ".ipynb"')
    if os.path.isfile(path):
        raise JupyvivError(f'Notebook "{path}" already exists')

    # metadata -----------------------------------------------------------------
    # metadata is retrieved into queue so we can await it
    metadata_queue = asyncio.Queue()

    async def recv_metadata(message: Message):
        await metadata_queue.put(json.loads(message.args))

    # agent communication setup
    send_queue = new_queue()
    handler = MessageHandler({"metadata": recv_metadata})

    async def run_communication():
        try:
            await run_client(agent_addr, handler, send_queue)
        except Exception:
            pass

    socket_task = asyncio.create_task(run_communication())

    # get metadata
    send_queue.put(Message("new", "get_metadata"))
    try:
        metadata = await asyncio.wait_for(metadata_queue.get(), timeout=10)
    except Exception:
        raise JupyvivError("Failed to retrieve metadata from agent")
    finally:
        socket_task.cancel()
        await socket_task

    # notebook -----------------------------------------------------------------
    # use jupyviv to get notebook structure with nbformat version + 1 empty cell
    jupytext_result = subprocess.run(
        ["jupytext", "--to", "notebook"],
        input="",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        notebook = json.loads(jupytext_result.stdout)
        notebook["metadata"] = metadata
        with open(path, "w") as fp:
            json.dump(notebook, fp)
    except Exception:
        raise JupyvivError("Failed to create notebook")

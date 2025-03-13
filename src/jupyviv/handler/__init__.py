import asyncio
import signal
import sys

from jupyviv.agent import launch_as_subprocess
from jupyviv.handler.sync import JupySync
from jupyviv.handler.vivify import viv_open
from jupyviv.shared.messages import MessageHandler, new_queue
from jupyviv.shared.transport.iostream import run as run_editor_com
from jupyviv.shared.transport.websocket import default_port, run_client as run_agent_com
from jupyviv.shared.utils import Subparsers

async def _main(notebook: str, agent_address: str | None, log_level: str):
    agent_proc = None
    try:
        with JupySync(notebook) as jupy_sync:
            viv_open(notebook)

            # lazy launch agent if address not provided
            if agent_address is None:
                agent_proc = launch_as_subprocess(jupy_sync.kernel_name, log_level)

            send_queue_editor = new_queue()
            send_queue_agent = new_queue()
            recv_handler_editor = MessageHandler({})
            recv_handler_agent = MessageHandler({})

            editor_task = asyncio.create_task(run_editor_com(recv_handler_editor, send_queue_editor, sys.stdin, sys.stdout))
            try:
                await run_agent_com(agent_address or f'localhost:{default_port}', recv_handler_agent, send_queue_agent)
            except asyncio.CancelledError: # keyboard interrupt
                editor_task.cancel()
                await editor_task
    finally:
        # shut down lazily launched agent with handler
        if agent_proc is not None:
            agent_proc.send_signal(signal.SIGINT)

def _cli(args):
    try:
        asyncio.run(_main(args.notebook, args.agent, args.log))
    except KeyboardInterrupt:
        pass

def setup_handler_args(subparsers: Subparsers):
    parser = subparsers.add_parser('handler', help='Run the handler')
    parser.add_argument('notebook', type=str)
    parser.add_argument('--agent', type=str, help='Address to connect to a running agent')
    parser.set_defaults(func=_cli)

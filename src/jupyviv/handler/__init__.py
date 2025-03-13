import asyncio
import sys

from jupyviv.handler.sync import JupySync
from jupyviv.handler.vivify import viv_open
from jupyviv.shared.messages import Message, MessageHandler, new_queue
from jupyviv.shared.transport.iostream import run
from jupyviv.shared.utils import Subparsers

async def _main(notebook: str, agent_address: str | None):
    with JupySync(notebook) as jupy_sync:
        viv_open(notebook)

        send_queue = new_queue()
        recv_handler = MessageHandler({})

        try:
            await run(recv_handler, send_queue, sys.stdin, sys.stdout)
        except asyncio.CancelledError: # keyboard interrupt
            pass

def _cli(args):
    asyncio.run(_main(args.notebook, args.agent))

def setup_handler_args(subparsers: Subparsers):
    parser = subparsers.add_parser('handler', help='Run the handler')
    parser.add_argument('notebook', type=str)
    parser.add_argument('--agent', type=str, help='Address to connect to a running agent')
    parser.set_defaults(func=_cli)

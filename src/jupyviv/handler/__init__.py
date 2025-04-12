import asyncio
import sys

from jupyviv.agent import launch_as_subprocess
from jupyviv.handler.endpoints import setup_endpoints
from jupyviv.handler.sync import JupySync
from jupyviv.handler.vivify import viv_open
from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import MessageHandler, new_queue
from jupyviv.shared.transport.iostream import run as run_editor_com
from jupyviv.shared.transport.websocket import default_port, run_client as run_agent_com
from jupyviv.shared.utils import Subparsers

_logger = get_logger(__name__)

async def main(args):
    try:
        with JupySync(args.notebook) as jupy_sync:
            viv_open(args.notebook)

            # lazy launch agent if address not provided (will quit automatically when parent dies)
            if args.agent is None:
                launch_as_subprocess(jupy_sync.kernel_name, args.log, False)

            send_queue_editor = new_queue()
            send_queue_agent = new_queue()

            handlers_editor, handlers_agent = setup_endpoints(jupy_sync, send_queue_editor, send_queue_agent)
            recv_handler_editor = MessageHandler(handlers_editor)
            recv_handler_agent = MessageHandler(handlers_agent)

            editor_task = asyncio.create_task(run_editor_com(recv_handler_editor, send_queue_editor, sys.stdin, sys.stdout))
            try:
                await run_agent_com(args.agent or f'localhost:{default_port}', recv_handler_agent, send_queue_agent)
            except asyncio.CancelledError: # keyboard interrupt
                editor_task.cancel()
                await editor_task
    except Exception as e:
        _logger.critical(e)

def setup_handler_args(subparsers: Subparsers):
    parser = subparsers.add_parser('handler', help='Run the handler')
    parser.add_argument('notebook', type=str)
    parser.add_argument('--agent', type=str, help='Address to connect to a running agent')
    parser.set_defaults(func=main)

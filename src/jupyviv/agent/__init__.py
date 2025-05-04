import asyncio
import subprocess
import sys

from jupyviv.agent.kernel import setup_kernel
from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import MessageHandler, new_queue
from jupyviv.shared.transport.websocket import default_port, run_server
from jupyviv.shared.utils import Subparsers

_logger = get_logger(__name__)

async def main(args):
    try:
        send_queue = new_queue()
        handlers, run_kernel = await setup_kernel(args.kernel_name, send_queue)

        recv_handler = MessageHandler(handlers)
        server_task = asyncio.create_task(run_server(args.port, recv_handler, send_queue))

        try:
            await run_kernel()
        except asyncio.CancelledError: # keyboard interrupt
            server_task.cancel()
            await server_task
    except Exception as e:
        _logger.critical(e)
        return 1

async def launch_as_subprocess(kernel_name: str, log_level: str, outlive_parent: bool) -> asyncio.subprocess.Process:
    return await asyncio.create_subprocess_exec(
        sys.argv[0],
        '--log', log_level, '--outlive-parent' if outlive_parent else '--no-outlive-parent',
        'agent', kernel_name,
        stderr=sys.stderr, stdout=subprocess.DEVNULL
    )

def setup_agent_args(subparsers: Subparsers):
    parser = subparsers.add_parser('agent', help='Run the agent')
    parser.add_argument('kernel_name', type=str, help='Name of the kernel to run')
    parser.add_argument('--port', type=int, default=default_port, help='Port to run the agent on')
    parser.set_defaults(func=main)

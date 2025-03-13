import asyncio
import subprocess
import sys

from jupyviv.agent.kernel import setup_kernel
from jupyviv.shared.messages import MessageHandler, new_queue
from jupyviv.shared.transport.websocket import default_port, run_server
from jupyviv.shared.utils import Subparsers

async def _main(port: int, kernel_name: str):
    send_queue = new_queue()
    handlers, run_kernel = await setup_kernel(kernel_name, send_queue)

    recv_handler = MessageHandler(handlers)
    server_task = asyncio.create_task(run_server(port, recv_handler, send_queue))

    try:
        await run_kernel()
    except asyncio.CancelledError: # keyboard interrupt
        server_task.cancel()
        await server_task

def _cli(args):
    try:
        asyncio.run(_main(args.port, args.kernel_name))
    except KeyboardInterrupt:
        pass

def launch_as_subprocess(kernel_name: str, log_level: str) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.argv[0], '--log', log_level, 'agent', kernel_name],
        stderr=sys.stderr,
        stdout=subprocess.DEVNULL
    )

def setup_agent_args(subparsers: Subparsers):
    parser = subparsers.add_parser('agent', help='Run the agent')
    parser.add_argument('kernel_name', type=str, help='Name of the kernel to run')
    parser.add_argument('--port', type=int, default=default_port, help='Port to run the agent on')
    parser.set_defaults(func=_cli)

import asyncio
from jupyviv.agent.kernel import setup_kernel
from jupyviv.shared.messages import MessageQueue, Message
from jupyviv.shared.transport.websocket import run_server
from jupyviv.shared.utils import Subparsers

async def _main(port: int, kernel_name: str):
    send_queue: MessageQueue = asyncio.Queue[Message]()
    recv_handler, run_kernel = await setup_kernel(kernel_name, send_queue)

    server_task = asyncio.create_task(run_server(port, recv_handler, send_queue))

    try:
        await run_kernel()
    except KeyboardInterrupt:
        server_task.cancel()

def _cli(args):
    asyncio.run(_main(args.port, args.kernel_name))

def setup_agent_args(subparsers: Subparsers):
    parser = subparsers.add_parser('agent', help='Run the agent')
    parser.add_argument('kernel_name', type=str, help='Name of the kernel to run')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the agent on')
    parser.set_defaults(func=_cli)

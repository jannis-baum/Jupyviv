import argparse
import asyncio
import collections
import os
import subprocess
import sys
import time

from jupyviv.agent.kernel import setup_kernel
from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import Message, MessageHandler, new_queue
from jupyviv.shared.transport.websocket import default_port, run_server
from jupyviv.shared.utils import Subparsers

_logger = get_logger(__name__)

_start_time = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
_cache_dir = os.path.expanduser(os.path.join("~", ".cache", "jupyviv"))
_persistent_queue_name = f"agent_{_start_time}_queue.txt"
_persistent_queue_path = os.path.join(_cache_dir, _persistent_queue_name)


def _persist_deque(deque: collections.deque[Message]):
    # remove file if empty
    if not deque and os.path.exists(_persistent_queue_path):
        os.remove(_persistent_queue_path)
        return

    store_str = "".join([message.to_str() + "\0\n" for message in list(deque)])
    os.makedirs(_cache_dir, exist_ok=True)
    with open(_persistent_queue_path, "w") as fp:
        fp.write(store_str)


async def main(args):
    try:
        send_queue = new_queue()
        if args.persist_unsent_messages:
            send_queue.change_handler = _persist_deque

        handlers, run_kernel = await setup_kernel(args.kernel_name, send_queue)

        recv_handler = MessageHandler(handlers)
        server_task = asyncio.create_task(
            run_server(args.port, recv_handler, send_queue)
        )

        try:
            await run_kernel()
        except asyncio.CancelledError:  # keyboard interrupt
            server_task.cancel()
            await server_task
    except Exception as e:
        _logger.critical(e)
        return 1


async def launch_as_subprocess(
    kernel_name: str, log_level: str, outlive_parent: bool
) -> asyncio.subprocess.Process:
    return await asyncio.create_subprocess_exec(
        sys.argv[0],
        "--log",
        log_level,
        "--outlive-parent" if outlive_parent else "--no-outlive-parent",
        "agent",
        "--no-persist-unsent-messages",
        kernel_name,
        stderr=sys.stderr,
        stdout=subprocess.DEVNULL,
    )


def setup_agent_args(subparsers: Subparsers):
    parser = subparsers.add_parser("agent", help="Run the agent")
    parser.add_argument("kernel_name", type=str, help="Name of the kernel to run")
    parser.add_argument(
        "--port", type=int, default=default_port, help="Port to run the agent on"
    )
    parser.add_argument(
        "--persist-unsent-messages",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=f"Persist unsent messages in {_cache_dir}, enabled by default",
    )
    parser.set_defaults(func=main)

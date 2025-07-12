import asyncio
import sys

from jupyviv.agent import launch_as_subprocess
from jupyviv.handler.endpoints import setup_endpoints
from jupyviv.handler.new import create_notebook
from jupyviv.handler.sync import JupySync
from jupyviv.handler.vivify import viv_open
from jupyviv.shared.errors import JupyvivError
from jupyviv.shared.lifetime import shutdown
from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import MessageHandler, new_queue
from jupyviv.shared.transport.iostream import run as run_editor_com
from jupyviv.shared.transport.websocket import default_port
from jupyviv.shared.transport.websocket import run_client as run_agent_com
from jupyviv.shared.utils import Subparsers

_logger = get_logger(__name__)


# lazy launch agent (will quit automatically when parent dies)
async def _launch_agent(kernel_name: str, log: str):
    proc = await launch_as_subprocess(kernel_name, log, False)

    # agent shoudn't terminate on its own; if it does terminate handler
    async def _handle_agent_stop():
        await proc.wait()
        _logger.critical("Agent exited")
        await shutdown()

    asyncio.create_task(_handle_agent_stop())


def get_agent_addr(arg: str | None) -> str:
    if arg is None or arg == "":
        return f"localhost:{default_port}"
    if ":" in arg:
        return arg
    return f"{arg}:{default_port}"


async def main(args):
    should_launch_agent = args.agent is None
    agent_addr = get_agent_addr(args.agent)
    if args.new is not None:
        # ensure agent is running & new argument is correct
        if should_launch_agent:
            if args.new is True:
                _logger.critical(
                    "--new [KERNEL_NAME] has to be specified if --agent is not"
                )
                return 1
            kernel_name = str(args.new)
            await _launch_agent(kernel_name, args.log)
            should_launch_agent = False
        else:
            if args.new is not True:
                _logger.critical(
                    "--new [KERNEL_NAME] can only be specified if --agent is not"
                )
                return 1
        # create new notebook
        try:
            await create_notebook(args.notebook, agent_addr)
        except JupyvivError as error:
            _logger.critical(str(error))
            return 1

    try:
        with JupySync(args.notebook) as jupy_sync:
            viv_open(args.notebook)
            if should_launch_agent:
                await _launch_agent(jupy_sync.kernel_name, args.log)

            send_queue_editor = new_queue()
            send_queue_agent = new_queue()

            handlers_editor, handlers_agent = setup_endpoints(
                jupy_sync, send_queue_editor, send_queue_agent
            )
            recv_handler_editor = MessageHandler(handlers_editor)
            recv_handler_agent = MessageHandler(handlers_agent)

            editor_task = asyncio.create_task(
                run_editor_com(
                    recv_handler_editor, send_queue_editor, sys.stdin, sys.stdout
                )
            )
            try:
                await run_agent_com(agent_addr, recv_handler_agent, send_queue_agent)
            except asyncio.CancelledError:  # keyboard interrupt
                editor_task.cancel()
                await editor_task
                return 0
    except Exception as e:
        _logger.critical(e)
        return 1


async def absorb(args):
    try:
        with open(args.queue, "r") as fp:
            message_strs = fp.read().split("\0\n")[:-1]

        with JupySync(args.notebook) as jupy_sync:
            viv_open(args.notebook)

            _, handlers_agent = setup_endpoints(jupy_sync, new_queue(), new_queue())
            recv_handler_agent = MessageHandler(handlers_agent)

            try:
                for message_str in message_strs:
                    await recv_handler_agent.handle(message_str)
            except asyncio.CancelledError:  # keyboard interrupt
                return 0
    except Exception as e:
        _logger.critical(e)
        return 1


def setup_handler_args(subparsers: Subparsers):
    parser_handler = subparsers.add_parser("handler", help="Run the handler")
    parser_handler.add_argument("notebook", type=str)
    parser_handler.add_argument(
        "--agent",
        type=str,
        nargs="?",
        help="Address to connect to a running agent. Omitting port uses the default port. Providing an empty address uses localhost with the default port.",
    )
    parser_handler.add_argument(
        "--new",
        nargs="?",
        const=True,
        metavar="KERNEL_NAME",
        help="Create a new notebook. Specify kernel name as argument iff not providing --agent",
    )
    parser_handler.set_defaults(func=main)

    parser_absorb = subparsers.add_parser(
        "absorb", help="Absorb an agent's queue into a Notebook"
    )
    parser_absorb.add_argument("queue", type=str)
    parser_absorb.add_argument("notebook", type=str)
    parser_absorb.set_defaults(func=absorb)

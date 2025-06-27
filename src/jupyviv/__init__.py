import argparse
import asyncio

from jupyviv.agent import setup_agent_args
from jupyviv.handler import setup_handler_args
from jupyviv.shared.lifetime import shutdown_with_parent
from jupyviv.shared.logs import default_log_level, log_levels, set_loglevel


async def main(parser, args):
    set_loglevel(args.log)

    if not args.outlive_parent:
        asyncio.create_task(shutdown_with_parent())

    if hasattr(args, "func"):
        return await args.func(args)
    parser.print_help()
    return 1


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log", choices=log_levels, default=default_log_level, help="Log level"
    )
    parser.add_argument(
        "--outlive-parent",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Keep running if parent process exits. Defaults to false",
    )

    # subparsers are passed to modules to add their own subcommands
    # have to specify 'args.func' to run the subcommand
    subparsers = parser.add_subparsers(help="Subcommand")
    setup_agent_args(subparsers)
    setup_handler_args(subparsers)

    args = parser.parse_args()

    try:
        return asyncio.run(main(parser, args))
    except KeyboardInterrupt:
        return 0

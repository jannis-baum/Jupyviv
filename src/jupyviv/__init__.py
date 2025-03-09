import argparse

from jupyviv.agent.cli import setup_agent_args
from jupyviv.shared.logs import set_loglevel

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', type=str, default='WARNING', help='Log level')
    parser.print_help

    # subparsers are passed to modules to add their own subcommands
    # have to specify 'args.func' to run the subcommand
    subparsers = parser.add_subparsers(help='Subcommand')
    setup_agent_args(subparsers)

    args = parser.parse_args()

    set_loglevel(args.log)

    if hasattr(args, 'func'):
        return args.func(args)
    parser.print_help()
    return 1

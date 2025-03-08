import argparse

from jupyviv.shared.logs import set_loglevel

type Subparsers = argparse._SubParsersAction[argparse.ArgumentParser]

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', type=str, default='WARNING', help='Log level')
    parser.print_help

    # subparsers are passed to modules to add their own subcommands
    # have to specify 'args.func' to run the subcommand
    subparsers = parser.add_subparsers(help='Subcommand')

    args = parser.parse_args()

    set_loglevel(args.log)

    if hasattr(args, 'func'):
        return args.func(args)
    parser.print_help()
    return 1

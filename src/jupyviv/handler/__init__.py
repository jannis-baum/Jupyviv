from jupyviv.shared.utils import Subparsers

async def _main(notebook: str, agent_address: str | None):
    pass

def _cli(args):
    pass

def setup_handler_args(subparsers: Subparsers):
    parser = subparsers.add_parser('handler', help='Run the handler')
    parser.add_argument('notebook', type=str)
    parser.add_argument('--agent', type=str, help='Address to connect to a running agent')
    parser.set_defaults(func=_cli)

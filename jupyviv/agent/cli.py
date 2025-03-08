from jupyviv.shared.utils import Subparsers

def run_agent(args):
    print('Running agent. args:', args)

def setup_agent_args(subparsers: Subparsers):
    parser = subparsers.add_parser('agent', help='Run the agent')
    parser.add_argument('kernel_name', type=str, help='Name of the kernel to run')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the agent on')
    parser.set_defaults(func=run_agent)

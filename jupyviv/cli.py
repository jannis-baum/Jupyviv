import argparse

from jupyviv.communication import run
from jupyviv.endpoints import setup_endpoints
from jupyviv.kernel import Kernel
from jupyviv.logs import set_loglevel
from jupyviv.sync import JupySync
from jupyviv.vivify import viv_open, viv_reload


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', type=str)
    parser.add_argument('--log', type=str, default='WARNING', help='Log level')
    args = parser.parse_args()

    set_loglevel(args.log)

    with JupySync(args.notebook) as jupy_sync, Kernel() as kernel:
        viv_open(args.notebook)
        endpoints = setup_endpoints(jupy_sync, kernel, lambda: viv_reload(args.notebook))
        run(endpoints)

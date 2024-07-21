import argparse

from bottle import run

from jupyviv.app import setup_bottle
from jupyviv.kernel import Kernel
from jupyviv.sync import JupySync
from jupyviv.vivify import viv_open, viv_port, viv_reload
from jupyviv.logs import set_loglevel


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', type=str)
    parser.add_argument('--log', type=str, default='WARNING', help='Log level')
    args = parser.parse_args()

    set_loglevel(args.log)

    with JupySync(args.notebook) as jupy_sync, Kernel() as kernel:
        viv_open(args.notebook)
        app = setup_bottle(jupy_sync, kernel, lambda: viv_reload(args.notebook))
        run(app, host='localhost', port=viv_port + 1)

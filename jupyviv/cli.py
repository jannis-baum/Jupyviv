import argparse
import logging

from bottle import run

from jupyviv.app import setup_bottle
from jupyviv.sync import JupySync
from jupyviv.vivify import viv_open, viv_port, viv_reload


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', type=str)
    parser.add_argument('--log', type=str, default='WARNING', help='Logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.log)

    with JupySync(args.notebook) as jupy_sync:
        viv_open(args.notebook)
        app = setup_bottle(jupy_sync, lambda: viv_reload(args.notebook))
        run(app, host='localhost', port=viv_port + 1)

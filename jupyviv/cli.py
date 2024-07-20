import argparse
import logging
import time

from jupyviv.sync import JupySync


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', type=str)
    parser.add_argument('--log', type=str, default='WARNING', help='Logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.log)

    with JupySync(args.notebook) as jupy_sync:
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

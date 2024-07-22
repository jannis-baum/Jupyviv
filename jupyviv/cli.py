import argparse

from jupyviv.communication import JupyVivError, run
from jupyviv.endpoints import setup_endpoints
from jupyviv.kernel import Kernel
from jupyviv.logs import set_loglevel, get_logger
from jupyviv.sync import JupySync
from jupyviv.vivify import viv_open, viv_reload

logger = get_logger(__name__)

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', type=str)
    parser.add_argument('--log', type=str, default='WARNING', help='Log level')
    args = parser.parse_args()

    set_loglevel(args.log)

    try:
        with JupySync(args.notebook) as jupy_sync, Kernel(jupy_sync.kernel_name) as kernel:
            viv_open(args.notebook)
            endpoints = setup_endpoints(jupy_sync, kernel, lambda: viv_reload(args.notebook))
            run(endpoints)
    except JupyVivError as e:
        logger.critical(e)
        exit(1)

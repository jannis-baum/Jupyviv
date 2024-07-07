import argparse
import time

from src.sync import JupySync


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', type=str)
    args = parser.parse_args()

    with JupySync(args.notebook) as jupy_sync:
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

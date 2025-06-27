import os
import subprocess

import requests

from jupyviv.shared.logs import get_logger

_logger = get_logger(__name__)

try:
    viv_port = int(os.environ.get("VIV_PORT", ""))
except Exception:
    viv_port = 31622
viv_url = f"http://localhost:{viv_port}"


def viv_open(file: str):
    subprocess.call(["viv", file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def viv_reload(file: str):
    path = os.path.realpath(file)
    try:
        requests.post(f"{viv_url}/viewer{path}", json={"reload": 1})
    except Exception as e:
        _logger.error(f"Failed to reload {path} in Vivify: {e}")
        pass

import os
import subprocess

import requests

viv_port = os.environ.get('VIV_PORT', 31622)
viv_url = f'http://localhost:{viv_port}'

def viv_open(file: str):
    subprocess.call(['viv', file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def viv_reload(file: str):
    path = os.path.realpath(file)
    try:
        requests.post(f'{viv_url}/viewer{path}', json={'reload': 1})
    except Exception as e:
        print(e)
        pass

import os
import subprocess

viv_port = os.environ.get('VIV_PORT', 31622)
viv_url = f'http://localhost:{viv_port}'

def viv_open(file: str):
    subprocess.call(['viv', file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

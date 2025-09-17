import subprocess


def viv_open(file: str):
    subprocess.call(["viv", file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

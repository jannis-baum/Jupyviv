from pprint import pprint

from src.kernel import Kernel

with Kernel() as k:
    pprint(k.execute('print("Hello World!")'))

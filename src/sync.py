import os
import shutil

from jupytext.cli import jupytext

class JupySync:
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f'Notebook "{path}" not found')
        if not path.endswith('.ipynb'):
            raise ValueError('Notebook must have .ipynb extension')

        self.nb_original = path
        temp = ''.join(path.split('.ipynb')[:-1]) + '.jupysync'
        self.nb_copy = temp + '.ipynb'
        self.py = temp + '.py'

    def __enter__(self):
        shutil.copy(self.nb_original, self.nb_copy)
        jupytext(['--set-formats', 'ipynb,py:percent', self.nb_copy])

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.remove(self.nb_copy)
        os.remove(self.py)

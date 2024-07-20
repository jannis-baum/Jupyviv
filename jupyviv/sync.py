import json
import logging
import os
import shutil

from jupytext.cell_reader import BaseCellReader
from jupytext.cli import jupytext as jupytext_cli

def _jupytext(*args: str):
    jupytext_cli(['--quiet', *args])

def _multiline_string(s: str | list[str]) -> str:
    if isinstance(s, str):
        return s
    return '\n'.join(s)

class JupySync():
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f'Notebook "{path}" not found')
        if not path.endswith('.ipynb'):
            raise ValueError('Notebook must have .ipynb extension')

        self.nb_original = path
        temp = ''.join(path.split('.ipynb')[:-1]) + '.jupyviv'
        self.nb_copy = temp + '.ipynb'
        self.py = temp + '.py'
        self.py_abs = os.path.abspath(self.py)

    def __enter__(self):
        # we work with a copied notebook for syncing to avoid adding jupytext
        # metadata to the original and/or version control
        shutil.copy(self.nb_original, self.nb_copy)
        _jupytext('--set-formats', 'ipynb,py:percent', self.nb_copy)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.remove(self.nb_copy)
        os.remove(self.py)

    def sync(self):
        logging.info(f'Syncing')

        # wrap BaseCellReader.read to save line numbers for each cell
        self.line2cell = list[int]()
        bcr_read = getattr(BaseCellReader, 'read')
        def bcr_read_wrapper(*args, **kwargs):
            # seek to first cell, header is assigned cell -1
            if len(self.line2cell) == 0:
                first_line = args[1][0] + '\n'
                with open(self.py, 'r') as fp:
                    for line in fp.readlines():
                        self.line2cell.append(-1)
                        if line == first_line: break
            # save line numbers for next cell
            result = bcr_read(*args, **kwargs)
            self.line2cell += [self.line2cell[-1] + 1] * result[1]
            return result
        setattr(BaseCellReader, 'read', bcr_read_wrapper)

        # sync to copied notebook
        _jupytext('--sync', self.py)

        # restore BaseCellReader.read
        setattr(BaseCellReader, 'read', bcr_read)

        # copy synced notebook to original, remove metadata
        shutil.copy(self.nb_copy, self.nb_original)
        _jupytext(self.nb_original, '--update-metadata', '{"jupytext":null}')

    def code_for_cell_at_line(self, line: int) -> str | None:
        if line in self.line2cell:
            return None
        with open(self.nb_copy, 'r') as fp:
            nb = json.load(fp)
            cell = nb['cells'][self.line2cell[line]]
            return _multiline_string(cell['source'])

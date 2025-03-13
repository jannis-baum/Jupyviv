import json
import os
import shutil

from jupytext.cell_reader import BaseCellReader
from jupytext.cli import jupytext as jupytext_cli

from jupyviv.shared.errors import JupyVivError
from jupyviv.shared.logs import get_logger
from jupyviv.shared.utils import dsafe

_logger = get_logger(__name__)

def _jupytext(*args: str):
    jupytext_cli(['--quiet', *args])

def _multiline_string(s: str | list[str]) -> str:
    if isinstance(s, str):
        return s
    return '\n'.join(s)

class JupyVivCellIndexError(JupyVivError):
    def __init__(self, i: int):
        super().__init__(f'Cell {i} out of bounds')

class JupySync():
    def __init__(self, path):
        if not os.path.exists(path):
            raise JupyVivError(f'Notebook "{path}" not found')
        if not path.endswith('.ipynb'):
            raise JupyVivError('Notebook must have .ipynb extension')
        with open(path, 'r') as fp:
            nb_data = json.load(fp)

            self.format = dsafe(nb_data, 'metadata', 'language_info', 'file_extension')
            if self.format == None or not isinstance(self.format, str) or not self.format.startswith('.'):
                raise JupyVivError('Invalid metadata language_info.file_extension')
            self.format = self.format[1:]

            kernel_name = dsafe(nb_data, 'metadata', 'kernelspec', 'name')
            if kernel_name == None or not isinstance(kernel_name, str):
                raise JupyVivError('Invalid metadata kernelspec.name')
            self.kernel_name = str(kernel_name)

        self.nb_original = path
        temp = ''.join(path.split('.ipynb')[:-1]) + '.jupyviv'
        self.nb_copy = temp + '.ipynb'
        self.script = f'{temp}.{self.format}'

    def __enter__(self):
        # we work with a copied notebook for syncing to avoid adding jupytext
        # metadata to the original and/or version control
        shutil.copy(self.nb_original, self.nb_copy)
        _jupytext('--set-formats', f'ipynb,{self.format}:percent', self.nb_copy)
        self.sync()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.remove(self.nb_copy)
        os.remove(self.script)

    def _sync_script(self):
        # wrap BaseCellReader.read to save line numbers for each cell
        self.line2cell = list[int]()
        bcr_read = getattr(BaseCellReader, 'read')
        def bcr_read_wrapper(*args, **kwargs):
            # seek to first cell, header is assigned cell -1
            if len(self.line2cell) == 0:
                first_line = args[1][0] + '\n'
                with open(self.script, 'r') as fp:
                    for line in fp.readlines():
                        self.line2cell.append(-1)
                        if line == first_line: break
            # save line numbers for next cell
            result = bcr_read(*args, **kwargs)
            self.line2cell += [self.line2cell[-1] + 1] * result[1]
            return result
        setattr(BaseCellReader, 'read', bcr_read_wrapper)

        # sync to copied notebook
        _jupytext('--sync', self.script)

        # restore BaseCellReader.read
        setattr(BaseCellReader, 'read', bcr_read)

    # sync notebook copy to original (e.g. after setting exec data)
    # script: sync script to notebook copy first
    def sync(self, script: bool = True):
        _logger.info(f'Syncing {"notebook and script" if script else "notebook"}')
        if script: self._sync_script()

        # copy synced notebook to original, remove metadata
        shutil.copy(self.nb_copy, self.nb_original)
        _jupytext(self.nb_original, '--update-metadata', '{"jupytext":null}')

    def code_for_cell(self, i: int) -> str:
        with open(self.nb_copy, 'r') as fp:
            cells = json.load(fp)['cells']
            if i >= len(cells):
                raise JupyVivCellIndexError(i)
            return _multiline_string(cells[i]['source'])

    def set_cell_exec_data(self, i: int, exec_count: int | None, outputs: list):
        with open(self.nb_copy, 'r') as fp:
            nb = json.load(fp)
            if i >= len(nb['cells']):
                raise JupyVivCellIndexError(i)
        nb['cells'][i]['execution_count'] = exec_count
        nb['cells'][i]['outputs'] = outputs
        with open(self.nb_copy, 'w') as fp:
            json.dump(nb, fp, indent=2)

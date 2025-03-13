import json
import os
import shutil
from typing import Any, Callable

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
        self._line2cell = list[str | None]()
        bcr_read = getattr(BaseCellReader, 'read')
        def bcr_read_wrapper(*args, **kwargs):
            # find start of first cell (below JupyText header)
            if len(self._line2cell) == 0:
                with open(self.script, 'r') as fp:
                    file_len = sum(1 for _ in fp)
                # args[1] is a list of all lines without the header
                header_len = file_len - len(args[1])
                self._line2cell += [None] * header_len

            # save line numbers for next cell
            cell, n_lines = bcr_read(*args, **kwargs)
            self._line2cell += [cell['id']] * n_lines
            return cell, n_lines
        setattr(BaseCellReader, 'read', bcr_read_wrapper)

        # sync to copied notebook
        _jupytext('--sync', self.script)

        # restore BaseCellReader.read
        setattr(BaseCellReader, 'read', bcr_read)

    # index of cell & notebook content
    def _find_cell(self, id: str) -> tuple[int, dict]:
        with open(self.nb_copy, 'r') as fp:
            nb = json.load(fp)
        for idx, cell in enumerate(nb['cells']):
            if cell['id'] == id:
                return idx, nb
        raise JupyVivError(f'Cell with id {id} not found')

    def cell_at(self, line: int) -> str:
        cell_id = self._line2cell[line]
        if cell_id is None:
            raise LookupError(f'No cell at line {line}')
        return cell_id

    # sync notebook copy to original (e.g. after setting exec data)
    # script: sync script to notebook copy first
    def sync(self, script: bool = True):
        _logger.info(f'Syncing {"notebook and script" if script else "notebook"}')
        if script: self._sync_script()

        # copy synced notebook to original, remove metadata
        shutil.copy(self.nb_copy, self.nb_original)
        _jupytext(self.nb_original, '--update-metadata', '{"jupytext":null}')

    def code_for_cell(self, id: str) -> str:
        idx, nb = self._find_cell(id)
        return _multiline_string(nb['cells'][idx]['source'])

    def modify_cell(self, id: str, f: Callable[[dict], dict]):
        idx, nb = self._find_cell(id)
        cell = f(nb['cells'][idx])
        nb['cells'][idx] = cell
        with open(self.nb_copy, 'w') as fp:
            json.dump(nb, fp, indent=2)

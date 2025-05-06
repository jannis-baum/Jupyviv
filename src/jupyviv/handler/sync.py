import json
import os
from pathlib import Path
import shutil
from typing import Callable

from jupytext.cell_reader import BaseCellReader
from jupytext.cli import jupytext as jupytext_cli

from jupyviv.shared.errors import JupyvivError
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
            raise JupyvivError(f'Notebook "{path}" not found')
        if not path.endswith('.ipynb'):
            raise JupyvivError('Notebook must have .ipynb extension')
        with open(path, 'r') as fp:
            nb_data = json.load(fp)

            self.format = dsafe(nb_data, 'metadata', 'language_info', 'file_extension')
            if self.format == None or not isinstance(self.format, str) or not self.format.startswith('.'):
                raise JupyvivError('Invalid metadata language_info.file_extension')
            self.format = self.format[1:]

            kernel_name = dsafe(nb_data, 'metadata', 'kernelspec', 'name')
            if kernel_name == None or not isinstance(kernel_name, str):
                raise JupyvivError('Invalid metadata kernelspec.name')
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

    def _read_nb(self) -> dict:
        with open(self.nb_copy, 'r') as fp:
            return json.load(fp)

    def _write_nb(self, nb: dict):
        with open(self.nb_copy, 'w') as fp:
            json.dump(nb, fp, indent=2)

    # MARK: syncing ------------------------------------------------------------
    # --------------------------------------------------------------------------
    def _sync_script(self):
        # save original state of script so we can restore after syncing to
        # prevent any changes that are made to the file open in the editor
        script_file = Path(self.script)
        script_content = script_file.read_bytes()
        script_stat = script_file.stat()
        script_mtime = script_stat.st_mtime_ns
        script_atime = script_stat.st_atime_ns

        # wrap BaseCellReader.read to save line numbers for each cell.
        # first we map line numbers to cell indices because JupyText uses
        # different ids internally
        line2cell_idx = list[int]()
        bcr_read = getattr(BaseCellReader, 'read')
        def bcr_read_wrapper(*args, **kwargs):
            nonlocal line2cell_idx
            # find start of first cell (below JupyText header)
            if len(line2cell_idx) == 0:
                with open(self.script, 'r') as fp:
                    file_len = sum(1 for _ in fp)
                # args[1] is a list of all lines without the header
                header_len = file_len - len(args[1])
                line2cell_idx += [-1] * header_len

            cell, n_lines = bcr_read(*args, **kwargs)
            # save line numbers for next cell
            line2cell_idx += [line2cell_idx[-1] + 1] * n_lines
            return cell, n_lines
        setattr(BaseCellReader, 'read', bcr_read_wrapper)

        # sync to copied notebook
        _jupytext('--sync', self.script)

        # restore BaseCellReader.read
        setattr(BaseCellReader, 'read', bcr_read)

        # finally, we read the notebook and map the cell indices to the real
        # notebook cell ids
        nb = self._read_nb()
        self._line2cell = {
            line + 1: nb['cells'][cell_idx]['id']
            for line, cell_idx in enumerate(line2cell_idx)
        }

        # restore original state of script file (see above)
        script_file.write_bytes(script_content)
        os.utime(self.script, ns=(script_atime, script_mtime))

    # sync notebook copy to original (e.g. after setting exec data)
    # script: sync script to notebook copy first
    def sync(self, script: bool = True):
        _logger.info(f'Syncing {"notebook and script" if script else "notebook"}')
        if script: self._sync_script()

        # copy synced notebook to original, remove metadata
        shutil.copy(self.nb_copy, self.nb_original)
        _jupytext(self.nb_original, '--update-metadata', '{"jupytext":null}')

    # MARK: cell functions -----------------------------------------------------
    # --------------------------------------------------------------------------
    # index of cell & notebook content
    def _find_id(self, id: str) -> tuple[int, dict]:
        nb = self._read_nb()
        for idx, cell in enumerate(nb['cells']):
            if cell['id'] == id:
                return idx, nb
        raise JupyvivError(f'Cell with id {id} not found')

    def id_at_line(self, line: int) -> str:
        cell_id = self._line2cell[line]
        if cell_id is None:
            raise LookupError(f'No cell at line {line}')
        return cell_id

    def code_for_cell(self, cell: dict) -> str:
        return _multiline_string(cell['source'])

    def code_for_id(self, id: str) -> str:
        idx, nb = self._find_id(id)
        return self.code_for_cell(nb['cells'][idx])

    def modify_at_id(self, id: str, f: Callable[[dict], dict]):
        idx, nb = self._find_id(id)
        cell = f(nb['cells'][idx])
        nb['cells'][idx] = cell
        self._write_nb(nb)

    def modify_cells(self, f: Callable[[dict, int], dict]):
        nb = self._read_nb()
        cells = [f(cell, idx) for idx, cell in enumerate(nb['cells'])]
        nb['cells'] = cells
        self._write_nb(nb)

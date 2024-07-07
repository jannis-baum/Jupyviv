import logging
import os
import shutil

from jupytext.cli import jupytext as jupytext_cli
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

def _jupytext(*args: str):
    jupytext_cli(['--quiet', *args])

class JupySync(FileSystemEventHandler):
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f'Notebook "{path}" not found')
        if not path.endswith('.ipynb'):
            raise ValueError('Notebook must have .ipynb extension')

        self.nb_original = path
        temp = ''.join(path.split('.ipynb')[:-1]) + '.jupysync'
        self.nb_copy = temp + '.ipynb'
        self.py = temp + '.py'
        self.py_abs = os.path.abspath(self.py)

        self.observer = Observer()
        # if we don't set recursive=True, the observer will not detect any
        # changes
        self.observer.schedule(self, self.py, recursive=True)

    def __enter__(self):
        # we work with a copied notebook for syncing to avoid adding jupytext
        # metadata to the original and/or version control
        shutil.copy(self.nb_original, self.nb_copy)
        _jupytext('--set-formats', 'ipynb,py:percent', self.nb_copy)
        self.observer.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.observer.stop()
        self.observer.join()
        os.remove(self.nb_copy)
        os.remove(self.py)

    def sync(self):
        logging.info(f'Syncing')
        # sync to copied notebook, copy synced notebook, remove metadata
        _jupytext('--sync', self.py)
        shutil.copy(self.nb_copy, self.nb_original)
        _jupytext(self.nb_original, '--update-metadata', '{"jupytext":null}')

    # --------------------------------------------------------------------------
    # MARK: watchdog FileSystemEventHandler methods
    def on_modified(self, event):
        if self.py_abs == event.src_path:
            self.sync()

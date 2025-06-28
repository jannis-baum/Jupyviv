import json
import os
import pathlib

import pytest

from jupyviv.handler.sync import JupySync


# create temporary minimal notebook
@pytest.fixture
def notebook_path(tmp_path: pathlib.Path):
    notebook_path = tmp_path / "notebook.ipynb"
    notebook_path.write_text(
        json.dumps(
            {
                "cells": [],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3 (ipykernel)",
                        "language": "python",
                        "name": "python3",
                    },
                    "language_info": {
                        "codemirror_mode": {"name": "ipython", "version": 3},
                        "file_extension": ".py",
                        "mimetype": "text/x-python",
                        "name": "python",
                        "nbconvert_exporter": "python",
                        "pygments_lexer": "ipython3",
                        "version": "3.10.17",
                    },
                },
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
    )
    return notebook_path


# active jupy sync class
@pytest.fixture
def jupy_sync(notebook_path: pathlib.Path):
    with JupySync(str(notebook_path)) as jupy_sync:
        yield jupy_sync


def test_creates_files(jupy_sync: JupySync):
    assert os.path.exists(jupy_sync.nb_original)
    assert os.path.exists(jupy_sync.nb_copy)
    assert os.path.exists(jupy_sync.script)


def test_add_code(jupy_sync: JupySync):
    cells_before = jupy_sync.all_ids_and_code()
    assert len(cells_before) == 0

    code = "print('hehe')"
    with open(jupy_sync.script, "a") as fp:
        fp.write(code + "\n")
    jupy_sync.sync()

    cells_after = jupy_sync.all_ids_and_code()
    assert len(cells_after) == 1
    assert cells_after[0][1] == code

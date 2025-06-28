import json
import os
import pathlib
import uuid

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


def write_code(
    jupy_sync: JupySync, code: str = "print('hehe')", linebreak: bool = True
) -> str:
    with open(jupy_sync.script, "a") as fp:
        fp.write(code + "\n" if linebreak else code)
    return code


# code is synced into notebook file
def test_add_code_notebook(jupy_sync: JupySync):
    cells_before = jupy_sync.all_ids_and_code()
    assert len(cells_before) == 0

    code = write_code(jupy_sync)
    jupy_sync.sync()

    cells_after = jupy_sync.all_ids_and_code()
    assert len(cells_after) == 1
    assert cells_after[0][1] == code


# script file isn't modified in syncing
def test_add_code_script(jupy_sync: JupySync):
    write_code(jupy_sync)
    script_file = pathlib.Path(jupy_sync.script)
    content_before = script_file.read_bytes()
    stat_before = script_file.stat()

    jupy_sync.sync()

    stat_after = script_file.stat()

    assert script_file.read_bytes() == content_before
    assert stat_after.st_mtime_ns == stat_before.st_mtime_ns
    assert stat_after.st_atime_ns == stat_before.st_atime_ns


def test_cell_ids(jupy_sync: JupySync):
    code = write_code(jupy_sync)
    with open(jupy_sync.script, "r") as fp:
        n_lines = len(fp.readlines())

    jupy_sync.sync()

    id = jupy_sync.all_ids_and_code()[0][0]
    assert jupy_sync.id_at_line(n_lines) == id
    assert jupy_sync.code_for_id(id) == code


def test_metadata_preservation(jupy_sync: JupySync):
    write_code(jupy_sync)
    jupy_sync.sync()
    id = jupy_sync.all_ids_and_code()[0][0]

    # add metadata
    unique_content = str(uuid.uuid4())
    jupy_sync.modify_at_id(
        id,
        lambda cell: {
            **cell,
            "metadata": {**cell["metadata"], "jupyviv": {"hehe": unique_content}},
        },
    )
    jupy_sync.sync(script=False)

    # helper to check that metadata is there
    def _check_metadata():
        idx, nb = jupy_sync._find_id(id)
        cell = nb["cells"][idx]
        assert unique_content in repr(cell["metadata"])

    # check that metadata is there before adding code
    _check_metadata()

    # add code to cell & run again
    write_code(jupy_sync)
    jupy_sync.sync(script=True)
    _check_metadata()

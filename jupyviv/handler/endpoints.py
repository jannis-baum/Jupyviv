# pyright: reportCallIssue=false

from typing import Callable

from jupyviv.agent.kernel import Kernel
from jupyviv.handler.sync import JupySync
from jupyviv.handler.transport_editor import Handler
from jupyviv.shared.error import JupyVivError

def setup_endpoints(
    jupy_sync: JupySync,
    kernel: Kernel,
    reload: Callable[[], None]
) -> dict[str, Handler]:

    def get_script(_: list[str]):
        return jupy_sync.script

    def _sync(script: bool):
        jupy_sync.sync(script)
        reload()

    def sync(_: list[str]):
        _sync(script=True)

    def run(args: list[str]):
        try:
            if len(args) != 1:
                raise ValueError
            line_i = int(args[0])
            if line_i < 0 or line_i >= len(jupy_sync.line2cell):
                raise ValueError
        except ValueError:
            raise JupyVivError('Invalid line number')

        cell_i = jupy_sync.line2cell[line_i]

        jupy_sync.set_cell_exec_data(cell_i, None, [])
        _sync(script=False)

        code = jupy_sync.code_for_cell(cell_i)
        exec_count, outputs = kernel.execute(code)

        jupy_sync.set_cell_exec_data(cell_i, exec_count, outputs)
        _sync(script=False)

    return {
        'sync': sync,
        'run': run,
        'get_script': get_script,
    }

# pyright: reportCallIssue=false

from typing import Callable

from jupyviv.communication import Handler, JupyVivError
from jupyviv.kernel import Kernel
from jupyviv.sync import JupySync

def setup_endpoints(
    jupy_sync: JupySync,
    kernel: Kernel,
    reload: Callable[[], None]
) -> dict[str, Handler]:

    def sync(_: list[str]):
        jupy_sync.sync()
        reload()

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
        code = jupy_sync.code_for_cell(cell_i)
        exec_count, outputs = kernel.execute(code)
        jupy_sync.set_cell_exec_data(cell_i, exec_count, outputs)
        sync([])

    return {
        'sync': sync,
        'run': run
    }

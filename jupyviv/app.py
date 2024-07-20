# pyright: reportCallIssue=false

from typing import Callable

from bottle import Bottle, abort

from jupyviv.sync import JupySync
from jupyviv.kernel import Kernel

_success = 'success'

def setup_bottle(jupy_sync: JupySync, kernel: Kernel, reload: Callable[[], None]):
    app = Bottle()

    @app.post('/sync')
    def sync():
        jupy_sync.sync()
        reload()
        return _success

    @app.post('/run/<line>')
    def run(line: str):
        print(line)
        try:
            line_i = int(line)
            if line_i < 0 or line_i >= len(jupy_sync.line2cell):
                raise ValueError
        except ValueError:
            print('abort')
            abort(400, 'Invalid line number')
            return

        cell_i = jupy_sync.line2cell[line_i]
        code = jupy_sync.code_for_cell(cell_i)
        exec_count, outputs = kernel.execute(code)
        jupy_sync.set_cell_exec_data(cell_i, exec_count, outputs)
        sync()
        return _success

    return app

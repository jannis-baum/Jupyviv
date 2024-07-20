# pyright: reportCallIssue=false

from typing import Callable

from bottle import Bottle

from jupyviv.sync import JupySync

def setup_bottle(jupy_sync: JupySync, reload: Callable[[], None]):
    app = Bottle()

    @app.post('/sync')
    def sync():
        jupy_sync.sync()
        reload()
        return 'success'

    return app

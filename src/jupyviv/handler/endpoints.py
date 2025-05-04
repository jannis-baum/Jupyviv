import json
from jupyviv.handler.sync import JupySync
from jupyviv.handler.vivify import viv_open, viv_reload
from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import Message, MessageHandlerDict, MessageQueue

_logger = get_logger(__name__)

# returns handlers for editor & agent
def setup_endpoints(
    jupy_sync: JupySync,
    send_queue_io: MessageQueue,
    send_queue_agent: MessageQueue
) -> tuple[MessageHandlerDict, MessageHandlerDict]:
    def _sync(script: bool):
        jupy_sync.sync(script)
        viv_reload(jupy_sync.nb_original)

    # EDITOR ENDPOINTS ---------------------------------------------------------
    async def get_script(message: Message):
        send_queue_io.put(Message(message.id, 'script', jupy_sync.script))

    async def open_notebook(_: Message):
        viv_open(jupy_sync.nb_original)

    async def sync(_: Message):
        _sync(script=True)

    async def run_at(message: Message):
        line_i = int(message.args)
        cell_id = jupy_sync.cell_at(line_i)
        code = jupy_sync.code_for_cell(cell_id)
        send_queue_agent.put(Message(cell_id, 'execute', code))

    async def interrupt(message: Message):
        send_queue_agent.put(Message(message.id, 'interrupt'))

    async def restart(message: Message):
        send_queue_agent.put(Message(message.id, 'restart'))

    handlers_io: MessageHandlerDict = {
        'script': get_script,
        'viv_open': open_notebook,
        'sync': sync,
        'run_at': run_at,
        'interrupt': interrupt,
        'restart': restart
    }

    # AGENT ENDPOINTS ----------------------------------------------------------
    async def status(message: Message):
        if message.args == 'busy':
            # start of execution: reset count & outputs, set custom isRunning
            jupy_sync.modify_cell(message.id, lambda cell: {
                **cell, 'execution_count': None, 'outputs': [], 'metadata': {
                    **cell['metadata'], 'jupyviv': { 'isRunning': True }
                }
            })
        if message.args == 'idle':
            # execution done, remove custom isRunning
            jupy_sync.modify_cell(message.id, lambda cell: {
                **cell, 'metadata': {
                    k: v for k, v in cell['metadata'].items() if k != 'jupyviv'
                }
            })
        _sync(False)

    async def execute_input(message: Message):
        jupy_sync.modify_cell(message.id, lambda cell: {
            **cell, 'execution_count': int(message.args)
        })
        _sync(False)

    async def output(message: Message):
        jupy_sync.modify_cell(message.id, lambda cell: {
            **cell, 'outputs': cell['outputs'] + [json.loads(message.args)]
        })
        _sync(False)

    handlers_agent: MessageHandlerDict = {
        'status': status,
        'execute_input': execute_input,
        'output': output
    }

    return handlers_io, handlers_agent

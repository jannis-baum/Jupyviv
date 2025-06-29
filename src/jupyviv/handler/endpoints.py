import json

from jupyviv.handler.sync import JupySync
from jupyviv.handler.vivify import viv_open, viv_reload
from jupyviv.shared.errors import JupyvivError
from jupyviv.shared.messages import Message, MessageHandlerDict, MessageQueue


# returns handlers for editor & agent
def setup_endpoints(
    jupy_sync: JupySync, send_queue_io: MessageQueue, send_queue_agent: MessageQueue
) -> tuple[MessageHandlerDict, MessageHandlerDict]:
    def _sync(script: bool):
        jupy_sync.sync(script)
        viv_reload(jupy_sync.nb_original)

    # EDITOR ENDPOINTS ---------------------------------------------------------
    async def get_script(message: Message):
        send_queue_io.put(Message(message.id, "script", jupy_sync.script))

    async def open_notebook(_: Message):
        viv_open(jupy_sync.nb_original)

    async def sync(_: Message):
        _sync(script=True)

    async def run_at(message: Message):
        line_i = int(message.args)
        cell_id = jupy_sync.id_at_line(line_i)
        code = jupy_sync.code_for_id(cell_id)
        send_queue_agent.put(Message(cell_id, "execute", code))

    async def run_between(message: Message):
        args = message.args.split(" ")
        if len(args) != 2:
            raise JupyvivError("Expected 2 arguments")
        start_i = int(args[0])
        end_i = int(args[1])
        # dicts preserve order and can't have duplicate keys (-> "ordered set")
        cell_ids = dict.fromkeys(
            jupy_sync.id_at_line(line_i) for line_i in range(start_i, end_i + 1)
        )
        for cell_id in cell_ids:
            # code_for_id on non-code cell raises error
            try:
                code = jupy_sync.code_for_id(cell_id)
            except JupyvivError:
                continue
            send_queue_agent.put(Message(cell_id, "execute", code))

    async def run_all(_: Message):
        ids_and_code = jupy_sync.all_ids_and_code()
        for cell_id, code in ids_and_code:
            send_queue_agent.put(Message(cell_id, "execute", code))

    async def interrupt(message: Message):
        send_queue_agent.put(Message(message.id, "interrupt"))

    async def restart(message: Message):
        send_queue_agent.put(Message(message.id, "restart"))

    async def clear_execution(_: Message):
        jupy_sync.clear_execution()
        _sync(False)

    async def enumerate_execution(_: Message):
        jupy_sync.enumerate_execution()
        _sync(False)

    handlers_io: MessageHandlerDict = {
        "script": get_script,
        "viv_open": open_notebook,
        "sync": sync,
        "run_at": run_at,
        "run_between": run_between,
        "run_all": run_all,
        "interrupt": interrupt,
        "restart": restart,
        "clear_execution": clear_execution,
        "enumerate_execution": enumerate_execution,
    }

    # AGENT ENDPOINTS ----------------------------------------------------------
    async def status(message: Message):
        if message.args == "busy":
            # start of execution: reset count & outputs, set custom isRunning
            jupy_sync.modify_at_id(
                message.id,
                lambda cell: {
                    **cell,
                    "execution_count": None,
                    "outputs": [],
                    "metadata": {**cell["metadata"], "jupyviv": {"isRunning": True}},
                },
            )
        if message.args == "idle":
            # execution done, remove custom isRunning
            jupy_sync.modify_at_id(
                message.id,
                lambda cell: {
                    **cell,
                    "metadata": {
                        k: v for k, v in cell["metadata"].items() if k != "jupyviv"
                    },
                },
            )
        _sync(False)

    async def execute_input(message: Message):
        jupy_sync.modify_at_id(
            message.id, lambda cell: {**cell, "execution_count": int(message.args)}
        )
        _sync(False)

    async def output(message: Message):
        jupy_sync.modify_at_id(
            message.id,
            lambda cell: {
                **cell,
                "outputs": cell["outputs"] + [json.loads(message.args)],
            },
        )
        _sync(False)

    handlers_agent: MessageHandlerDict = {
        "status": status,
        "execute_input": execute_input,
        "output": output,
    }

    return handlers_io, handlers_agent

from jupyter_client.blocking.client import BlockingKernelClient
from jupyter_client.manager import KernelManager

from jupyviv.shared.logs import get_logger
from jupyviv.shared.utils import dsafe

_logger = get_logger(__name__)

class Kernel:
    _output_msg_types = ['execute_result', 'display_data', 'stream', 'error']

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        _logger.info('Starting kernel')
        self._km: KernelManager = KernelManager(kernel_name=self.name)
        self._km.start_kernel()

        self._kc: BlockingKernelClient = self._km.client()
        self._kc.start_channels()
        self._kc.wait_for_ready()
        _logger.info('Kernel ready')

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._kc is not None:
            self._kc.stop_channels()
        if self._km is not None:
            self._km.shutdown_kernel()
        del self._kc
        del self._km

    # returns execution count & outputs
    def execute(self, code) -> tuple[int | None, list]:
        msg_id = self._kc.execute(code)
        messages = list()
        execution_count = None
        while True:
            try:
                msg = self._kc.get_iopub_msg()
                # message belongs to our execution request
                if dsafe(msg, 'parent_header', 'msg_id') == msg_id:
                    msg_type = dsafe(msg, 'msg_type')
                    content = dsafe(msg, 'content')
                    # kernel is back in idle -> done
                    if msg_type == 'status' and dsafe(content, 'execution_state') == 'idle':
                        break
                    if msg_type == 'execute_input':
                        execution_count = dsafe(content, 'execution_count')
                    # message is one of the output types for the Notebook
                    if msg_type in self._output_msg_types and type(content) == dict:
                        messages.append({ 'output_type': msg_type, **content })
            except KeyboardInterrupt:
                break
        return execution_count, messages

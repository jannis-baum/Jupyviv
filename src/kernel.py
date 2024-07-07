import logging

from jupyter_client.manager import KernelManager

# safely access d which may or may not be a dictionary at k which may be a key
# or a list of keys for nested dictionaries
def _dsafe(d, *k):
    if len(k) > 1:
        return _dsafe(_dsafe(d, k[0]), *k[1:])
    if len(k) == 1:
        return d[k[0]] if type(d) == dict and k[0] in d else None
    return d

class Kernel:
    _output_msg_types = ['execute_result', 'display_data', 'stream', 'error']

    def __enter__(self):
        logging.info('Starting kernel')
        self._km = KernelManager()
        self._km.start_kernel()

        self._kc = self._km.client()
        self._kc.start_channels()
        self._kc.wait_for_ready()
        logging.info('Kernel ready')

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._kc is not None:
            self._kc.stop_channels()
        if self._km is not None:
            self._km.shutdown_kernel()
        self._kc = None
        self._km = None

    # returns execution count & outputs
    def execute(self, code) -> tuple[int | None, list]:
        msg_id = self._kc.execute(code)
        messages = list()
        execution_count = None
        while True:
            try:
                msg = self._kc.get_iopub_msg()
                # message belongs to our execution request
                if _dsafe(msg, 'parent_header', 'msg_id') == msg_id:
                    msg_type = _dsafe(msg, 'msg_type')
                    content = _dsafe(msg, 'content')
                    # kernel is back in idle -> done
                    if msg_type == 'status' and _dsafe(content, 'execution_state') == 'idle':
                        break
                    if msg_type == 'execute_input':
                        execution_count = _dsafe(content, 'execution_count')
                    # message is one of the output types for the Notebook
                    if msg_type in self._output_msg_types and type(content) == dict:
                        messages.append({ 'output_type': msg_type, **content })
            except KeyboardInterrupt:
                break
        return execution_count, messages

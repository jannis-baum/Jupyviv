import asyncio

from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.connection import Connection
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from jupyviv.shared.messages import MessageHandler, MessageQueue, Message
from jupyviv.shared.logs import get_logger

_logger = get_logger(__name__)

# wrapper to pass dropped messages by reference for messages that were taken
# out of queue before disconnect/error
class _DroppedMessage():
    def __init__(self):
        self.message: Message | None = None

# create send/receive handler for server & client
async def _connection_handler(
    websocket: Connection,
    recv_handler: MessageHandler,
    send_queue: MessageQueue,
    dropped_message: _DroppedMessage
):
    async def _sender():
        message = None
        while True:
            try:
                if dropped_message.message is not None:
                    message = dropped_message.message
                    dropped_message.message = None
                else:
                    message = await send_queue.get()
                _logger.debug(f'Websocket sending message: {message}')
                await websocket.send(message.to_str())
                # clear message after successful send
                message = None
            except (ConnectionClosed, asyncio.CancelledError):
                dropped_message.message = message
                break
            except Exception as e:
                _logger.error(f'Send error {type(e)}: {e}')

    async def _receiver():
        try:
            async for message in websocket:
                try:
                    _logger.debug(f'IO received message string: {str(message)}')
                    await recv_handler.handle(str(message))
                except Exception as e:
                    _logger.error(f'Receive error {type(e)}: {e}')
        except (ConnectionClosed, asyncio.CancelledError):
            pass

    sender_task = asyncio.create_task(_sender())
    # receiver exits on ConnectionClose, we use that to cancel sender as well
    await _receiver()
    sender_task.cancel()
    await sender_task

default_port = 8000

async def run_server(
    port: int,
    recv_handler: MessageHandler,
    send_queue: MessageQueue
):
    # message that was dropped due to disconnect or other errors
    dropped_message = _DroppedMessage()
    is_connected = False
    async def connection_handler(websocket: ServerConnection):
        # restrict to single connection
        nonlocal is_connected
        if is_connected:
            await websocket.close(1002) # 1002: Protocol Error
            return
        is_connected = True
        # keep track of connection closing
        try:
            await _connection_handler(websocket, recv_handler, send_queue, dropped_message)
        finally:
            is_connected = False

    async with serve(connection_handler, 'localhost', port) as server:
        await server.serve_forever()

async def run_client(
    address: str,
    recv_handler: MessageHandler,
    send_queue: MessageQueue,
    connection_retries = 5
):
    # message that was dropped due to disconnect or other errors
    dropped_message = _DroppedMessage()
    async def consumer(websocket: ClientConnection):
        await _connection_handler(websocket, recv_handler, send_queue, dropped_message)

    for attempt in range(connection_retries):
        try:
            async with connect(f'ws://{address}') as websocket:
                await consumer(websocket)
            break
        except OSError:
            if attempt == connection_retries - 1:
                raise
            await asyncio.sleep(1)
            continue

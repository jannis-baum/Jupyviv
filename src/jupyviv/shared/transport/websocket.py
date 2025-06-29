import asyncio

from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.connection import Connection
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import MessageHandler, MessageQueue

_logger = get_logger(__name__)
_max_msg_size = 50 * 1000 * 1000  # 50MB


# create send/receive handler for server & client
async def _connection_handler(
    websocket: Connection,
    recv_handler: MessageHandler,
    send_queue: MessageQueue,
):
    async def _sender():
        message = None
        while True:
            try:
                message = await send_queue.popleft()
                _logger.debug(f"Websocket sending message: {message}")
                await websocket.send(message.to_str())
                # clear message after successful send
                message = None
            except (ConnectionClosed, asyncio.CancelledError):
                if message is not None:
                    send_queue.putleft(message)
                break
            except Exception as e:
                _logger.error(f"Send error {type(e)}: {e}")

    async def _receiver():
        try:
            async for message in websocket:
                try:
                    _logger.debug(f"IO received message with length: {len(message)}")
                    await recv_handler.handle(str(message))
                except Exception as e:
                    _logger.error(f"Receive error {type(e)}: {e}")
        except (ConnectionClosed, asyncio.CancelledError):
            pass

    sender_task = asyncio.create_task(_sender())
    # receiver exits on ConnectionClose, we use that to cancel sender as well
    await _receiver()
    sender_task.cancel()
    await sender_task


# one after vivify
default_port = 31623


async def run_server(port: int, recv_handler: MessageHandler, send_queue: MessageQueue):
    # message that was dropped due to disconnect or other errors
    is_connected = False

    async def connection_handler(websocket: ServerConnection):
        # restrict to single connection
        nonlocal is_connected
        if is_connected:
            await websocket.close(1002)  # 1002: Protocol Error
            return
        is_connected = True
        # keep track of connection closing
        try:
            await _connection_handler(websocket, recv_handler, send_queue)
        finally:
            is_connected = False

    async with serve(
        connection_handler, "localhost", port, max_size=_max_msg_size
    ) as server:
        await server.serve_forever()


async def run_client(
    address: str,
    recv_handler: MessageHandler,
    send_queue: MessageQueue,
    connection_retries=5,
):
    # message that was dropped due to disconnect or other errors
    async def consumer(websocket: ClientConnection):
        await _connection_handler(websocket, recv_handler, send_queue)

    for attempt in range(connection_retries):
        try:
            async with connect(f"ws://{address}", max_size=_max_msg_size) as websocket:
                await consumer(websocket)
            break
        except OSError:
            if attempt == connection_retries - 1:
                raise
            await asyncio.sleep(1)
            continue

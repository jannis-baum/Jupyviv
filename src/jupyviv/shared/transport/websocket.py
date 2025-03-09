import asyncio

from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.connection import Connection
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from jupyviv.shared.messages import AsyncMessageHandler, AsyncMessageQueue
from jupyviv.shared.logs import get_logger

_logger = get_logger(__name__)

# create send/receive handler for server & client
async def _connection_handler(
    websocket: Connection,
    recv_handler: AsyncMessageHandler,
    send_queue: AsyncMessageQueue
):
    async def _sender():
        while True:
            try:
                message = await send_queue.get()
                await websocket.send(message.to_str())
            except ConnectionClosed:
                break
            except Exception as e:
                _logger.error(f'Send error {type(e)}: {e}')

    async def _receiver():
        async for message in websocket:
            try:
                await recv_handler.handle(str(message))
            except ConnectionClosed:
                break
            except Exception as e:
                _logger.error(f'Receive error {type(e)}: {e}')

    await asyncio.gather(_sender(), _receiver())

async def run_server(
    port: int,
    recv_handler: AsyncMessageHandler,
    send_queue: AsyncMessageQueue
):
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
            await _connection_handler(websocket, recv_handler, send_queue)
        finally:
            is_connected = False

    async with serve(connection_handler, 'localhost', port) as server:
        await server.serve_forever()

async def run_client(
    host: str,
    port: int,
    recv_handler: AsyncMessageHandler,
    send_queue: AsyncMessageQueue
):
    async def consumer(websocket: ClientConnection):
        await _connection_handler(websocket, recv_handler, send_queue)

    async with connect(f'ws://{host}:{port}') as websocket:
        await consumer(websocket)

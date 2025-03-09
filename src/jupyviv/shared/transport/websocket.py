import asyncio

from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.connection import Connection
from websockets.asyncio.server import ServerConnection, serve

from jupyviv.shared.messages import AsyncMessageHandler, Message

# create send/receive handler for server & client
async def _connection_handler(
    websocket: Connection,
    recv_handler: AsyncMessageHandler,
    send_queue: asyncio.Queue[Message]
):
    async def _sender():
        while True:
            message = await send_queue.get()
            await websocket.send(message.to_str())

    async def _receiver():
        async for message in websocket:
            await recv_handler.handle(str(message))

    await asyncio.gather(_sender(), _receiver())

async def run_server(
    port: int,
    recv_handler: AsyncMessageHandler,
    send_queue: asyncio.Queue[Message]
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
    send_queue: asyncio.Queue[Message]
):
    async def consumer(websocket: ClientConnection):
        await _connection_handler(websocket, recv_handler, send_queue)

    async with connect(f'ws://{host}:{port}') as websocket:
        await consumer(websocket)

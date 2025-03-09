import asyncio
from typing import Awaitable, Callable

from websockets.asyncio.server import ServerConnection, serve

from jupyviv.shared.messages import AsyncMessageHandler, Message

def setup_server(port: int, handler: AsyncMessageHandler) -> Callable[[Message], Awaitable[None]]:
    websocket_ref: ServerConnection | None = None

    async def consumer(websocket: ServerConnection):
        nonlocal websocket_ref
        websocket_ref = websocket
        async for message in websocket:
            await handler.handle(str(message))

    async def run_server():
        async with serve(consumer, 'localhost', port) as server:
            await server.serve_forever()

    asyncio.run(run_server())

    async def send_message(message: Message):
        if websocket_ref is not None:
            await websocket_ref.send(message.to_str())

    return send_message

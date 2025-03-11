import asyncio
import sys
from typing import TextIO

from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import MessageHandler, MessageQueue

_logger = get_logger(__name__)

async def run(
    recv_handler: MessageHandler,
    send_queue: MessageQueue,
    read: TextIO = sys.stdin,
    write: TextIO = sys.stdout,
):
    async def _sender():
        while True:
            message = await send_queue.get()
            write.write(message.to_str())
            write.flush()

    async def _receiver():
        while True:
            message_str = read.readline()
            try:
                await recv_handler.handle(message_str)
            except Exception as e:
                _logger.error(f'Receive error {type(e)}: {e}')

    await asyncio.gather(_sender(), _receiver())

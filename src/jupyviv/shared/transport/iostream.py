import asyncio
import sys
from typing import TextIO

from jupyviv.shared.logs import get_logger
from jupyviv.shared.messages import MessageHandler, MessageQueue

_logger = get_logger(__name__)


async def _connect_iostream(
    read: TextIO, write: TextIO
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader()
    r_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: r_protocol, read)

    w_transport, w_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, write
    )
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)

    return reader, writer


async def run(
    recv_handler: MessageHandler,
    send_queue: MessageQueue,
    read: TextIO = sys.stdin,
    write: TextIO = sys.stdout,
):
    reader, writer = await _connect_iostream(read, write)

    async def _sender():
        while True:
            message = await send_queue.popleft()
            _logger.debug(f"IO sending message: {message}")
            writer.writelines([f"{message.to_str()}\n".encode()])

    async def _receiver():
        while not reader.at_eof():
            try:
                message_str = (await reader.readline()).decode()
                _logger.debug(f"IO received message string: {message_str}")
                await recv_handler.handle(message_str)
            except asyncio.CancelledError as e:
                raise e
            except Exception as e:
                _logger.error(f"Receive error {type(e)}: {e}")

    await asyncio.gather(_sender(), _receiver())

import asyncio
from typing import Awaitable, Callable, TypeVar

from jupyviv.shared.errors import JupyVivError

class MessageFormatError(JupyVivError):
    def __init__(self, message: str):
        super().__init__(f'Invalid message format: {message}')

class MessageUnknownError(JupyVivError):
    def __init__(self, command: str):
        super().__init__(f'Unknown command: {command}')

T = TypeVar("T")

class Message:
    def __init__(self, id: str, command: str, args: str):
        self.id = id
        self.command = command
        self.args = args

    @staticmethod
    def from_str(message_str: str):
        parts = message_str.split(' ')
        if len(parts) < 2:
            raise MessageFormatError(message_str)
        return Message(parts[0], parts[1], ' '.join(parts[2:]))

    def to_str(self):
        return ' '.join([str(self.id), self.command, self.args])

type MessageHandlerDict = dict[str, Callable[[Message], Awaitable[None]]]
class MessageHandler:
    def __init__(self, handlers: MessageHandlerDict):
        self.handlers = handlers

    async def handle(self, message_str: str):
        message = Message.from_str(message_str)
        handler = self.handlers.get(message.command)
        if handler is None:
            raise MessageUnknownError(message.command)
        await handler(message)

type MessageQueue = asyncio.Queue[Message]
def new_queue() -> MessageQueue:
    return asyncio.Queue[Message]()

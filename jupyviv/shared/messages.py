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
    def __init__(self, id: int, command: str, args: list[str]):
        self.id = id
        self.command = command
        self._args = args

    @staticmethod
    def from_str(message_str: str):
        parts = message_str.split(' ')
        if len(parts) < 2:
            raise MessageFormatError(message_str)
        try:
            id = int(parts[0])
        except ValueError:
            raise MessageFormatError(message_str)
        return Message(id, parts[1], parts[2:])

    def arg(self, index: int, constructor: Callable[[str], T]) -> T:
        try:
            return constructor(self._args[index])
        except (ValueError, IndexError):
            raise MessageFormatError(self.to_str())

    def to_str(self):
        return ' '.join([str(self.id), self.command, *self._args])

class MessageHandler:
    def __init__(self, handlers: dict[str, Callable[[Message], None]]):
        self.handlers = handlers

    def handle(self, message_str: str):
        message = Message.from_str(message_str)
        handler = self.handlers.get(message.command)
        if handler is None:
            raise MessageUnknownError(message.command)
        handler(message)

class AsyncMessageHandler:
    def __init__(self, handlers: dict[str, Callable[[Message], Awaitable[None]]]):
        self.handlers = handlers

    async def handle(self, message_str: str):
        message = Message.from_str(message_str)
        handler = self.handlers.get(message.command)
        if handler is None:
            raise MessageUnknownError(message.command)
        await handler(message)

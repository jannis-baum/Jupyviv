from typing import Awaitable, Callable

from jupyviv.shared.deque import Deque
from jupyviv.shared.errors import JupyvivError


class MessageFormatError(JupyvivError):
    def __init__(self, message: str):
        super().__init__(f"Invalid message format: {message}")


class MessageUnknownError(JupyvivError):
    def __init__(self, command: str):
        super().__init__(f"Unknown command: {command}")


class Message:
    def __init__(self, id: str, command: str, args: str = ""):
        self.id = id
        self.command = command
        self.args = args

    @staticmethod
    def from_str(message_str: str):
        parts = message_str.strip().split(" ")
        if len(parts) < 2:
            raise MessageFormatError(message_str)
        return Message(parts[0], parts[1], " ".join(parts[2:]))

    def to_str(self):
        return " ".join([str(self.id), self.command, self.args])


MessageHandlerDict = dict[str, Callable[[Message], Awaitable[None]]]


class MessageHandler:
    def __init__(self, handlers: MessageHandlerDict):
        self.handlers = handlers

    async def handle(self, message_str: str):
        message = Message.from_str(message_str)
        handler = self.handlers.get(message.command)
        if handler is None:
            raise MessageUnknownError(message.command)
        await handler(message)


MessageQueue = Deque[Message]


def new_queue() -> MessageQueue:
    return Deque[Message]()

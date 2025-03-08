from jupyviv.shared.errors import JupyVivError

class MessageFormatError(JupyVivError):
    def __init__(self, message: str):
        super().__init__(f'Invalid message format: {message}')

class Message:
    def __init__(self, id: int, command: str, args: list[str]):
        self.id = id
        self.command = command
        self._args = args

    @staticmethod
    def from_str(message: str, *types):
        parts = message.split(' ')
        try:
            id = int(parts[0])
        except ValueError:
            raise MessageFormatError(message)
        command = parts[1]

        raw_args = parts[2:]
        if len(raw_args) != len(types):
            raise MessageFormatError(f'{command} expects {len(types)} arguments')
        try:
            args = [t(arg) for t, arg in zip(types, raw_args)]
        except ValueError:
            raise MessageFormatError(f'{command} expects arguments of types {types}')

        return Message(id, command, args)

    def to_str(self):
        return ' '.join([str(self.id), self.command, *self._args])

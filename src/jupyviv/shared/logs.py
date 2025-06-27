import logging
import sys
from typing import Union

_registered_handlers = set[logging.StreamHandler]()

log_levels = {
    level: name for name, level in logging._nameToLevel.items() if level != 0
}.values()  # dict approach to remove duplicates (WARN, WARNING)
default_log_level = logging.getLevelName(logging.getLogger().level)


def set_loglevel(level: Union[str, int]):
    for handler in _registered_handlers:
        handler.setLevel(level)


# make loggers always output to stderr
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name.removeprefix("jupyviv."))
    logger.setLevel(logging.DEBUG)

    stderr_handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)
    _registered_handlers.add(stderr_handler)

    # ensure no handlers are added that output to stdout
    logger.propagate = False

    return logger

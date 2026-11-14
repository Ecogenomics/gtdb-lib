__version__ = '1.12.1'

import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"

# Configure only the logger used by gtdblib, rather than the root logger,
# so applications importing gtdblib keep control of their own logging.
log = logging.getLogger("rich")
if not log.handlers:
    _handler = RichHandler()
    _handler.setFormatter(logging.Formatter(FORMAT, datefmt="[%Y-%m-%d %H:%M:%S]"))
    log.addHandler(_handler)
    log.setLevel(logging.DEBUG)
    log.propagate = False

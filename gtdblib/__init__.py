__version__ = '1.10.1'

import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%Y-%m-%d %H:%M:%S]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

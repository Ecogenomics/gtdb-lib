__version__ = '1.10.1'

import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%Y-%m-%d %H:%M:%S]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

# Suppress requests and urllib3 logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

import logging
import os
from logging import handlers


LOGS_DIR = os.path.dirname(__file__) + "/../../bin/logs/"
'''Available loggers:
"_"
'''


def setup_logger(filename="CryptoWrapper", logger="_"):
    '''Set logger streams

    Optional params:
        filename: str = "CryptoWrapper"
        logger: str = "_"
    '''
    logger = logging.getLogger(logger)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
    # logging.raiseExceptions = False

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Logs stream to a new file daily
    filename = "{}/{}".format(LOGS_DIR, filename)
    hdlr = handlers.TimedRotatingFileHandler(
        filename=filename,
        when="midnight",
        interval=1,
        encoding="utf-8"
    )
    hdlr.suffix = "%Y_%m_%d.log"
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger

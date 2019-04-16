import logging
import os
from time import strftime, gmtime


LOGS_DIR = os.path.dirname(__file__) + "/../../bin/logs/"


def setup_logger(filename="CryptoWrapper", logger=""):
    '''Set logger streams

    Optional params:
        filename: str = "CryptoWrapper"
        logger: str = ""
    '''
    logger = logging.getLogger(logger)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
    # logging.raiseExceptions = False

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Logs stream to a file
    date = strftime("%Y_%m_%d", gmtime())
    hdlr = logging.FileHandler(
        f"{LOGS_DIR}/CryptoWrapper_{date}.log",
        encoding="utf-8"
    )
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger

#!/usr/bin/env python

import logging
import sys
import time


def setup_logging(log_file=None, log_level=None):
    """
    setup logging
    """
    if log_level and type(log_level) in [str]:
        log_level = log_level.upper()
        log_level = getattr(logging, log_level)
    else:
        log_level = logging.INFO

    if log_file:
        logging.basicConfig(
            filename=log_file,
            level=log_level,
            format="%(asctime)s\t%(threadName)s\t%(name)s\t%(levelname)s\t%(message)s",
        )
    else:
        logging.basicConfig(
            stream=sys.stdout,
            level=log_level,
            format="%(asctime)s\t%(threadName)s\t%(name)s\t%(levelname)s\t%(message)s",
        )

    logging.Formatter.converter = time.gmtime

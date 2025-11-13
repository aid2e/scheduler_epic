#!/usr/bin/env python

import logging
import sys
import time


import inspect

def write_function_to_file(func, path):
    """Write a standalone version of a user-defined function to a Python file."""
    func_source = inspect.getsource(func).strip()

    with open(path, "w") as f:
        f.write(func_source + "\n")

    return path


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


def list_to_tuple(data):
    if isinstance(data, list):
        return tuple(list_to_tuple(item) for item in data)
    elif isinstance(data, dict):
        return {key: list_to_tuple(value) for key, value in data.items()}
    else:
        return data

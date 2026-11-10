""" 
Logger Module 
"""

import logging 

def get_logger():
    """create and return application logger.
    """
    logger = logging.getLogger("ASRA")
    if logger.hasHandlers():
         return logger
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("[%(levelname)s] %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


"""
Logging.
"""

import sys

import oras.logger
from loguru import logger

from releases.core.constants import APP


def configure(verbose: bool) -> None:
    """
    Log to stderr when verbose. Stay quiet otherwise.
    """
    # Drop the stderr sink that loguru adds on import.
    logger.remove()
    oras.logger.setup_logger(quiet=not verbose, debug=verbose)
    if not verbose:
        logger.disable(APP)
        return

    logger.enable(APP)
    logger.add(sys.stderr, level="DEBUG")

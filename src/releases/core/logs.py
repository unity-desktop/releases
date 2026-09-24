"""
Logging.
"""

import sys

import oras.logger
from loguru import logger


def configure(verbose: bool) -> None:
    """
    Log progress to stderr. Add debug logs when verbose.
    """
    # Replace the stderr sink that loguru adds on import.
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if verbose else "INFO")
    oras.logger.setup_logger(quiet=not verbose, debug=verbose)

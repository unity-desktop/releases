"""
Errors.
"""


class ReleasesError(RuntimeError):
    """
    Base error.
    """


class SuiteError(ReleasesError):
    """
    Missing or invalid suite file.
    """


class RegistryError(ReleasesError):
    """
    Failed registry request.
    """

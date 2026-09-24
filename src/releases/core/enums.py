"""
Enums.
"""

from enum import StrEnum


class Status(StrEnum):
    """
    Effect of an upload on the published suite.
    """

    NEW = "new"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    UNCHANGED = "unchanged"
    REMOVED = "removed"

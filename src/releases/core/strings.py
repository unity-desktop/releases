"""
Strings that must match a pattern.
"""

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class PatternStr(str):
    """
    A str that must match PATTERN. Subclasses set PATTERN.
    """

    __slots__ = ()
    PATTERN = ".*"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """
        Check the pattern, then build the subclass.
        """
        return core_schema.no_info_after_validator_function(
            cls, core_schema.str_schema(pattern=cls.PATTERN)
        )

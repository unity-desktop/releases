"""
Base model for deb822 paragraphs.
"""

from debian.deb822 import Deb822
from pydantic import BaseModel, ConfigDict


class Stanza(BaseModel):
    """
    A deb822 paragraph. Subclasses set kind to their deb822 class.
    """

    # Let pydantic ignore kind, a class attribute that holds a class.
    model_config = ConfigDict(frozen=True, extra="ignore", ignored_types=(type,))

    kind = Deb822

    @classmethod
    def read[S: Stanza](cls: type[S], text: str) -> S:
        """
        Validate one paragraph.
        """
        return cls.validate_paragraph(cls.kind(text))

    @classmethod
    def read_all[S: Stanza](cls: type[S], text: str) -> list[S]:
        """
        Validate each paragraph of an index.
        """
        return [
            cls.validate_paragraph(paragraph)
            for paragraph in cls.kind.iter_paragraphs(text, use_apt_pkg=False)
        ]

    @classmethod
    def validate_paragraph[S: Stanza](cls: type[S], paragraph: Deb822) -> S:
        """
        Validate a parsed paragraph.
        """
        # Multivalued fields hold Deb822Dicts. pydantic wants plain dicts.
        return cls.model_validate(
            {
                key: [dict(line) for line in value] if isinstance(value, list) else value
                for key, value in paragraph.items()
            }
        )

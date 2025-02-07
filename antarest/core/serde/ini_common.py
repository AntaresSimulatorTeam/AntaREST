import dataclasses
from typing import Optional

PrimitiveType = str | int | float | bool


@dataclasses.dataclass(frozen=True)
class OptionMatcher:
    """
    Used to match a location in an INI file:
    a None section means any section.
    """

    section: Optional[str]
    key: str


def any_section_option_matcher(key: str) -> OptionMatcher:
    """
    Return a matcher which will match the provided key in any section.
    """
    return OptionMatcher(section=None, key=key)

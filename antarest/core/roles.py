import enum
import functools

__all__ = ["RoleType"]


@functools.total_ordering
class RoleType(enum.Enum):
    """
    Role type privilege

    Usage:

    >>> from antarest.core.roles import RoleType

    >>> RoleType.ADMIN == RoleType.ADMIN
    True
    >>> RoleType.ADMIN == RoleType.WRITER
    False
    >>> RoleType.ADMIN > RoleType.WRITER
    True
    >>> RoleType.ADMIN >= RoleType.WRITER
    True
    """

    ADMIN = 40
    WRITER = 30
    RUNNER = 20
    READER = 10

    def __ge__(self, other: object) -> bool:
        """
        Returns `True` if the current role has same or greater privilege than other role.
        """

        if isinstance(other, RoleType):
            return self.value >= other.value
        elif isinstance(other, int):
            return self.value >= other
        else:
            raise NotImplemented

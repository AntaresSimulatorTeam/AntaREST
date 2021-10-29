import enum

__all__ = ["RoleType"]


class RoleType(enum.Enum):
    """
    Role type privilege
    """

    ADMIN = 40
    RUNNER = 30
    WRITER = 20
    READER = 10

    def is_higher_or_equals(self, other: "RoleType") -> bool:
        return int(self.value) >= int(other.value)

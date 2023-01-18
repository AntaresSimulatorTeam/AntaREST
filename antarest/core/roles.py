import enum

__all__ = ["RoleType"]


class RoleType(enum.Enum):
    """
    Role type privilege
    """

    ADMIN = 40
    WRITER = 30
    RUNNER = 20
    READER = 10

    def is_higher_or_equals(self, other: "RoleType") -> bool:
        return int(self.value) >= int(other.value)

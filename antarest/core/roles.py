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

    @staticmethod
    def from_dict(value: int) -> "RoleType":
        mapping = {
            40: RoleType.ADMIN,
            30: RoleType.RUNNER,
            20: RoleType.WRITER,
            10: RoleType.READER,
        }

        if value in mapping:
            return mapping[value]
        else:
            raise ValueError(f"any role for value {value}")

    def to_dict(self) -> int:
        return int(self.value)

    def is_higher_or_equals(self, other: "RoleType") -> bool:
        return int(self.value) >= int(other.value)

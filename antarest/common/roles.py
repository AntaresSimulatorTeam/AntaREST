import enum

__all__ = ["RoleType"]


class RoleType(enum.Enum):
    ADMIN = 1
    RUNNER = 2
    WRITER = 3
    READER = 4

    @staticmethod
    def from_dict(value: int) -> "RoleType":
        mapping = {
            1: RoleType.ADMIN,
            2: RoleType.RUNNER,
            3: RoleType.WRITER,
            4: RoleType.READER,
        }

        if value in mapping:
            return mapping[value]
        else:
            raise ValueError(f"any role for value {value}")

    def to_dict(self) -> int:
        return int(self.value)

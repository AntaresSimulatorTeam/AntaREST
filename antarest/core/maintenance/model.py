from enum import Enum


class MaintenanceMode(str, Enum):
    NORMAL_MODE = "NORMAL"
    MAINTENANCE_MODE = "MAINTENANCE"

    @classmethod
    def from_bool(cls, flag: bool) -> "MaintenanceMode":
        return {False: cls.NORMAL_MODE, True: cls.MAINTENANCE_MODE}[flag]

    def __bool__(self) -> bool:
        cls = self.__class__
        return {cls.NORMAL_MODE: False, cls.MAINTENANCE_MODE: True}[self]

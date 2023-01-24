from enum import Enum


class MaintenanceMode(str, Enum):
    NORMAL_MODE = "NORMAL"
    MAINTENANCE_MODE = "MAINTENANCE"

    @staticmethod
    def to_str(element: bool) -> str:
        if element:
            return MaintenanceMode.MAINTENANCE_MODE.value
        return MaintenanceMode.NORMAL_MODE.value

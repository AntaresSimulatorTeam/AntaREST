from typing import Optional, List

from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.maintenance.model import MaintenanceDTO


class MaintenanceRepository(ConfigDataRepository):
    def save_maintenance_mode(self, mode: str) -> None:
        super().save(
            ConfigData(key=str(ConfigDataAppKeys.MAINTENANCE_MODE), value=mode)
        )

    def save_maintenance_message(self, message: str) -> None:
        super().save(
            ConfigData(
                key=str(ConfigDataAppKeys.MAINTENANCE_MESSAGE), value=message
            )
        )

    def save_maintenance_status(self, maintenance: MaintenanceDTO) -> None:
        super().save(
            ConfigData(
                key=str(ConfigDataAppKeys.MAINTENANCE_MODE),
                value=str(maintenance.mode),
            )
        )
        super().save(
            ConfigData(
                key=str(ConfigDataAppKeys.MAINTENANCE_MESSAGE),
                value=maintenance.message,
            )
        )

    def get_maintenance_status(self) -> Optional[MaintenanceDTO]:
        config_data: List[ConfigData] = super().get(
            [
                str(ConfigDataAppKeys.MAINTENANCE_MODE),
                str(ConfigDataAppKeys.MAINTENANCE_MESSAGE),
            ]
        )
        if len(config_data) == 2:
            mode = (
                config_data[0].value
                if config_data[0].key == ConfigDataAppKeys.MAINTENANCE_MODE
                else config_data[1].value
            )
            message = (
                config_data[0].value
                if config_data[0].key == ConfigDataAppKeys.MAINTENANCE_MESSAGE
                else config_data[1].value
            )
            return MaintenanceDTO(mode=mode, message=message)
        return None

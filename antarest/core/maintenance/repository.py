from typing import Optional, List

from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
from antarest.core.configdata.repository import ConfigDataRepository


class MaintenanceRepository(ConfigDataRepository):
    def save_maintenance_mode(self, mode: str) -> None:
        self.save(
            ConfigData(key=str(ConfigDataAppKeys.MAINTENANCE_MODE), value=mode)
        )

    def save_message_info(self, message: str) -> None:
        self.save(
            ConfigData(key=str(ConfigDataAppKeys.MESSAGE_INFO), value=message)
        )

    def get_maintenance_mode(self) -> Optional[str]:
        config_data: ConfigData = self.get(
            str(ConfigDataAppKeys.MAINTENANCE_MODE),
        )
        if config_data is not None:
            return config_data.value
        return None

    def get_message_info(self) -> Optional[str]:
        config_data: ConfigData = self.get(
            str(ConfigDataAppKeys.MESSAGE_INFO),
        )
        if config_data is not None:
            return config_data.value
        return None

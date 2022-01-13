from typing import Optional, List

from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
from antarest.core.configdata.repository import ConfigDataRepository


class MaintenanceRepository(ConfigDataRepository):
    def save_maintenance_mode(self, owner: int, mode: str) -> None:
        self.save(
            ConfigData(
                owner=owner,
                key=ConfigDataAppKeys.MAINTENANCE_MODE.value,
                value=mode,
            )
        )

    def save_message_info(self, owner: int, message: str) -> None:
        self.save(
            ConfigData(
                owner=owner,
                key=ConfigDataAppKeys.MESSAGE_INFO.value,
                value=message,
            )
        )

    def get_maintenance_mode(self, owner: int) -> Optional[str]:
        config_data = self.get(
            owner=owner,
            key=ConfigDataAppKeys.MAINTENANCE_MODE.value,
        )
        if config_data is not None:
            return str(config_data.value)
        return None

    def get_message_info(self, owner: int) -> Optional[str]:
        config_data = self.get(
            owner=owner,
            key=ConfigDataAppKeys.MESSAGE_INFO.value,
        )
        if config_data is not None:
            return str(config_data.value)
        return None

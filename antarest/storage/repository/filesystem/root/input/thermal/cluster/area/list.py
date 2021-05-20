from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class InputThermalClustersAreaList(IniFileNode):
    def __init__(self, config: StudyConfig, area: str):
        section = {
            "name": str,
            "group": str,
            "unitcount": int,
            "nominalcapacity": float,
            "market-bid-cost": float,
        }
        types = {ther: section for ther in config.get_thermal_names(area)}
        IniFileNode.__init__(self, config, types)

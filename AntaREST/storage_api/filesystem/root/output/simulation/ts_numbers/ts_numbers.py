from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.output.simulation.ts_numbers.hydro.hydro import (
    OutputSimulationTsNumbersHydro,
)
from AntaREST.storage_api.filesystem.root.output.simulation.ts_numbers.load.load import (
    OutputSimulationTsNumbersLoad,
)
from AntaREST.storage_api.filesystem.root.output.simulation.ts_numbers.solar.solar import (
    OutputSimulationTsNumbersSolar,
)
from AntaREST.storage_api.filesystem.root.output.simulation.ts_numbers.thermal.thermal import (
    OutputSimulationTsNumbersThermal,
)
from AntaREST.storage_api.filesystem.root.output.simulation.ts_numbers.wind.wind import (
    OutputSimulationTsNumbersWind,
)


class OutputSimulationTsNumbers(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "hydro": OutputSimulationTsNumbersHydro(config.next_file("hydro")),
            "load": OutputSimulationTsNumbersLoad(config.next_file("load")),
            "solar": OutputSimulationTsNumbersSolar(config.next_file("solar")),
            "wind": OutputSimulationTsNumbersWind(config.next_file("wind")),
            "thermal": OutputSimulationTsNumbersThermal(
                config.next_file("thermal")
            ),
        }
        return children

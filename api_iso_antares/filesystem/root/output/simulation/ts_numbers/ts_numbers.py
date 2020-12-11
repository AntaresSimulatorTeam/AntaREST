from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.ts_numbers.hydro.hydro import (
    OutputSimulationTsNumbersHydro,
)
from api_iso_antares.filesystem.root.output.simulation.ts_numbers.load.load import (
    OutputSimulationTsNumbersLoad,
)
from api_iso_antares.filesystem.root.output.simulation.ts_numbers.solar.solar import (
    OutputSimulationTsNumbersSolar,
)
from api_iso_antares.filesystem.root.output.simulation.ts_numbers.thermal.thermal import (
    OutputSimulationTsNumbersThermal,
)
from api_iso_antares.filesystem.root.output.simulation.ts_numbers.wind.wind import (
    OutputSimulationTsNumbersWind,
)


class OutputSimulationTsNumbers(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "hydro": OutputSimulationTsNumbersHydro(config.next_file("hydro")),
            "load": OutputSimulationTsNumbersLoad(config.next_file("load")),
            "solar": OutputSimulationTsNumbersSolar(config.next_file("solar")),
            "wind": OutputSimulationTsNumbersWind(config.next_file("wind")),
            "thermal": OutputSimulationTsNumbersThermal(
                config.next_file("thermal")
            ),
        }
        FolderNode.__init__(self, config, children)

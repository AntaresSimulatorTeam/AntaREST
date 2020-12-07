from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.hydro.prepro.area.energy import (
    InputHydroPreproAreaEnergy,
)
from api_iso_antares.domain.study.root.input.hydro.prepro.area.prepro import (
    InputHydroPreproAreaPrepro,
)


class InputHydroPreproArea(FolderNode):
    def __init__(self, config: Config):
        children = {
            "energy": InputHydroPreproAreaEnergy(
                config.next_file("energy.txt")
            ),
            "prepro": InputHydroPreproAreaPrepro(
                config.next_file("prepro.ini")
            ),
        }
        FolderNode.__init__(self, children)

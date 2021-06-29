from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.areas.areas import (
    InputAreas,
)
from antarest.storage.repository.filesystem.root.input.bindingconstraints.bindingcontraints import (
    BindingConstraints,
)
from antarest.storage.repository.filesystem.root.input.hydro.hydro import (
    InputHydro,
)
from antarest.storage.repository.filesystem.root.input.link.link import (
    InputLink,
)
from antarest.storage.repository.filesystem.root.input.load.load import (
    InputLoad,
)
from antarest.storage.repository.filesystem.root.input.miscgen.miscgen import (
    InputMiscGen,
)
from antarest.storage.repository.filesystem.root.input.reserves.reserves import (
    InputReserves,
)
from antarest.storage.repository.filesystem.root.input.solar.solar import (
    InputSolar,
)
from antarest.storage.repository.filesystem.root.input.thermal.thermal import (
    InputThermal,
)
from antarest.storage.repository.filesystem.root.input.wind.wind import (
    InputWind,
)


class Input(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "areas": InputAreas(self.context, config.next_file("areas")),
            "bindingconstraints": BindingConstraints(
                self.context, config.next_file("bindingconstraints")
            ),
            "hydro": InputHydro(self.context, config.next_file("hydro")),
            "links": InputLink(self.context, config.next_file("links")),
            "load": InputLoad(self.context, config.next_file("load")),
            "misc-gen": InputMiscGen(
                self.context, config.next_file("misc-gen")
            ),
            "reserves": InputReserves(
                self.context, config.next_file("reserves")
            ),
            "solar": InputSolar(self.context, config.next_file("solar")),
            "thermal": InputThermal(self.context, config.next_file("thermal")),
            "wind": InputWind(self.context, config.next_file("wind")),
        }
        return children

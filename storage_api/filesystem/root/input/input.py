from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.areas.areas import InputAreas
from storage_api.filesystem.root.input.bindingconstraints.bindingcontraints import (
    BindingConstraints,
)
from storage_api.filesystem.root.input.hydro.hydro import InputHydro
from storage_api.filesystem.root.input.link.link import InputLink
from storage_api.filesystem.root.input.load.load import InputLoad
from storage_api.filesystem.root.input.miscgen.miscgen import (
    InputMiscGen,
)
from storage_api.filesystem.root.input.reserves.reserves import (
    InputReserves,
)
from storage_api.filesystem.root.input.solar.solar import InputSolar
from storage_api.filesystem.root.input.thermal.thermal import (
    InputThermal,
)
from storage_api.filesystem.root.input.wind.wind import InputWind


class Input(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "areas": InputAreas(config.next_file("areas")),
            "bindingconstraints": BindingConstraints(
                config.next_file("bindingconstraints")
            ),
            "hydro": InputHydro(config.next_file("hydro")),
            "links": InputLink(config.next_file("links")),
            "load": InputLoad(config.next_file("load")),
            "misc-gen": InputMiscGen(config.next_file("misc-gen")),
            "reserves": InputReserves(config.next_file("reserves")),
            "solar": InputSolar(config.next_file("solar")),
            "thermal": InputThermal(config.next_file("thermal")),
            "wind": InputWind(config.next_file("wind")),
        }
        return children

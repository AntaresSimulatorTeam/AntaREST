from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.areas.areas import InputAreas
from api_iso_antares.filesystem.root.input.bindingconstraints.bindingcontraints import (
    BindingConstraints,
)
from api_iso_antares.filesystem.root.input.hydro.hydro import InputHydro
from api_iso_antares.filesystem.root.input.link.link import InputLink
from api_iso_antares.filesystem.root.input.load.load import InputLoad
from api_iso_antares.filesystem.root.input.miscgen.miscgen import (
    InputMiscGen,
)
from api_iso_antares.filesystem.root.input.reserves.reserves import (
    InputReserves,
)
from api_iso_antares.filesystem.root.input.solar.solar import InputSolar
from api_iso_antares.filesystem.root.input.thermal.thermal import (
    InputThermal,
)
from api_iso_antares.filesystem.root.input.wind.wind import InputWind


class Input(FolderNode):
    def __init__(self, config: Config):
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
        FolderNode.__init__(self, children)

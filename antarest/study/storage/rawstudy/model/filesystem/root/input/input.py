from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    ENR_MODELLING,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.areas import (
    InputAreas,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.bindingconstraints.bindingcontraints import (
    BindingConstraints,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.hydro import (
    InputHydro,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.link.link import (
    InputLink,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.load.load import (
    InputLoad,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.miscgen.miscgen import (
    InputMiscGen,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.renewables.renewable import (
    ClusteredRenewables,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.reserves.reserves import (
    InputReserves,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.solar.solar import (
    InputSolar,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.thermal import (
    InputThermal,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.wind import (
    InputWind,
)


class Input(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "areas": InputAreas(self.context, self.config.next_file("areas")),
            "bindingconstraints": BindingConstraints(
                self.context, self.config.next_file("bindingconstraints")
            ),
            "hydro": InputHydro(self.context, self.config.next_file("hydro")),
            "links": InputLink(self.context, self.config.next_file("links")),
            "load": InputLoad(self.context, self.config.next_file("load")),
            "misc-gen": InputMiscGen(
                self.context, self.config.next_file("misc-gen")
            ),
            "reserves": InputReserves(
                self.context, self.config.next_file("reserves")
            ),
            "solar": InputSolar(self.context, self.config.next_file("solar")),
            "thermal": InputThermal(
                self.context, self.config.next_file("thermal")
            ),
            "wind": InputWind(self.context, self.config.next_file("wind")),
        }

        if self.config.enr_modelling == ENR_MODELLING.CLUSTERS.value:
            children["renewables"] = ClusteredRenewables(
                self.context, self.config.next_file("renewables")
            )

        return children

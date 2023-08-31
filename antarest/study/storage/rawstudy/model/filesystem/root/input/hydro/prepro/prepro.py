from antarest.study.storage.rawstudy.model.filesystem.common.prepro import PreproCorrelation
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.prepro.area.area import InputHydroPreproArea


class InputHydroPrepro(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            a: InputHydroPreproArea(self.context, self.config.next_file(a)) for a in self.config.area_names()
        }
        children["correlation"] = PreproCorrelation(self.context, self.config.next_file("correlation.ini"))
        return children

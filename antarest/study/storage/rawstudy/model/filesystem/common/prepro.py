from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)


class PreproCorrelation(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {
            "general": {"mode": str},
            "0": {},
            "1": {},
            "2": {},
            "3": {},
            "4": {},
            "5": {},
            "6": {},
            "7": {},
            "8": {},
            "9": {},
            "10": {},
            "11": {},
        }
        IniFileNode.__init__(self, context, config, types)


class PreproAreaSettings(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(self, context, config, types={})


class PreproArea(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "conversion": InputSeriesMatrix(
                self.context, self.config.next_file("conversion.txt")
            ),
            "data": InputSeriesMatrix(
                self.context, self.config.next_file("data.txt")
            ),
            "k": InputSeriesMatrix(
                self.context, self.config.next_file("k.txt")
            ),
            "translation": InputSeriesMatrix(
                self.context, self.config.next_file("translation.txt")
            ),
            "settings": PreproAreaSettings(
                self.context, self.config.next_file("settings.ini")
            ),
        }
        return children


class InputPrepro(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            a: PreproArea(self.context, self.config.next_file(a))
            for a in self.config.area_names()
        }
        children["correlation"] = PreproCorrelation(
            self.context, self.config.next_file("correlation.ini")
        )
        return children

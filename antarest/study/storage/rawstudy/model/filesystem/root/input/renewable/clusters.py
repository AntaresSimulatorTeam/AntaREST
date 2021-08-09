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


class ClusteredRenewableClusterConfig(IniFileNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        section = {
            "name": str,
            "group": str,
            "enabled": bool,
            "unitcount": int,
            "nomialcapacity": 0,
            "ts-interpretation": str,
        }
        types = {
            renewable: section
            for renewable in config.get_renewable_names(area)
        }
        IniFileNode.__init__(self, context, config, types)


class ClusteredRenewableCluster(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self, config: FileStudyTreeConfig) -> TREE:
        return {
            "list": ClusteredRenewableClusterConfig(
                self.context, config.next_file("list.ini"), self.area
            )
        }


class ClusteredRenewableAreaCluster(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        return {
            area: ClusteredRenewableCluster(
                self.context, config.next_file(area), area
            )
            for area in config.area_names()
        }

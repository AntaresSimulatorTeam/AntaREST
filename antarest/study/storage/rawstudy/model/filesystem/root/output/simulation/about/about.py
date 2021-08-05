from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.about.parameters import (
    OutputSimulationAboutParameters,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.about.study import (
    OutputSimulationAboutStudy,
)


class OutputSimulationAbout(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "areas": RawFileNode(self.context, config.next_file("areas.txt")),
            "comments": RawFileNode(
                self.context, config.next_file("comments.txt")
            ),
            "links": RawFileNode(self.context, config.next_file("links.txt")),
            # TODO "map": OutputSimulationAboutMap(self.context, config.next_file("map")),
            "study": OutputSimulationAboutStudy(
                self.context, config.next_file("study.ini")
            ),
            "parameters": OutputSimulationAboutParameters(
                self.context, config.next_file("parameters.ini")
            ),
        }
        return children

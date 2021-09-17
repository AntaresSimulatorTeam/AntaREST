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
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.about.study import (
    OutputSimulationAboutStudy,
)
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    GeneralData,
)


class OutputSimulationAbout(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "areas": RawFileNode(
                self.context, self.config.next_file("areas.txt")
            ),
            "comments": RawFileNode(
                self.context, self.config.next_file("comments.txt")
            ),
            "links": RawFileNode(
                self.context, self.config.next_file("links.txt")
            ),
            # TODO "map": OutputSimulationAboutMap(self.context, self.config.next_file("map")),
            "study": OutputSimulationAboutStudy(
                self.context, self.config.next_file("study.ini")
            ),
            "parameters": GeneralData(
                self.context, self.config.next_file("parameters.ini")
            ),
        }
        return children

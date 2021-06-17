from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.about.areas import (
    OutputSimulationAboutAreas,
)
from antarest.storage.repository.filesystem.root.output.simulation.about.comments import (
    OutputSimulationAboutComments,
)
from antarest.storage.repository.filesystem.root.output.simulation.about.links import (
    OutputSimulationAboutLinks,
)
from antarest.storage.repository.filesystem.root.output.simulation.about.parameters import (
    OutputSimulationAboutParameters,
)
from antarest.storage.repository.filesystem.root.output.simulation.about.study import (
    OutputSimulationAboutStudy,
)


class OutputSimulationAbout(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "areas": OutputSimulationAboutAreas(
                self.context, config.next_file("areas.txt")
            ),
            "comments": OutputSimulationAboutComments(
                self.context, config.next_file("comments.txt")
            ),
            "links": OutputSimulationAboutLinks(
                self.context, config.next_file("links.txt")
            ),
            # TODO "map": OutputSimulationAboutMap(self.context, config.next_file("map")),
            "study": OutputSimulationAboutStudy(
                self.context, config.next_file("study.ini")
            ),
            "parameters": OutputSimulationAboutParameters(
                self.context, config.next_file("parameters.ini")
            ),
        }
        return children

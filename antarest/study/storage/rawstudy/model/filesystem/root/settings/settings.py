from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.settings.comments import (
    Comments,
)
from antarest.storage.business.rawstudy.model.filesystem.root.settings.generaldata import (
    GeneralData,
)
from antarest.storage.business.rawstudy.model.filesystem.root.settings.resources.resources import (
    Resources,
)
from antarest.storage.business.rawstudy.model.filesystem.root.settings.scenariobuilder import (
    ScenarioBuilder,
)
from antarest.storage.business.rawstudy.model.filesystem.root.settings.simulations.simulations import (
    SettingsSimulations,
)


class Settings(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "resources": Resources(
                self.context, config.next_file("resources")
            ),
            "simulations": SettingsSimulations(
                self.context, config.next_file("simulations")
            ),
            "comments": Comments(
                self.context, config.next_file("comments.txt")
            ),
            "generaldata": GeneralData(
                self.context, config.next_file("generaldata.ini")
            ),
            "scenariobuilder": ScenarioBuilder(
                self.context, config.next_file("scenariobuilder.dat")
            ),
        }
        return children

from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.settings.comments import Comments
from antarest.storage_api.filesystem.root.settings.generaldata import (
    GeneralData,
)
from antarest.storage_api.filesystem.root.settings.resources.resources import (
    Resources,
)
from antarest.storage_api.filesystem.root.settings.scenariobuilder import (
    ScenarioBuilder,
)
from antarest.storage_api.filesystem.root.settings.simulations.simulations import (
    SettingsSimulations,
)


class Settings(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "resources": Resources(config.next_file("resources")),
            "simulations": SettingsSimulations(
                config.next_file("simulations")
            ),
            "comments": Comments(config.next_file("comments.txt")),
            "generaldata": GeneralData(config.next_file("generaldata.ini")),
            "scenariobuilder": ScenarioBuilder(
                config.next_file("scenariobuilder.dat")
            ),
        }
        return children

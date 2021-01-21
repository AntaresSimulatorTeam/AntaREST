from typing import Optional

from storage_api.custom_types import JSON
from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.settings.comments import Comments
from storage_api.filesystem.root.settings.generaldata import GeneralData
from storage_api.filesystem.root.settings.resources.resources import (
    Resources,
)
from storage_api.filesystem.root.settings.scenariobuilder import (
    ScenarioBuilder,
)
from storage_api.filesystem.root.settings.simulations.simulations import (
    SettingsSimulations,
)


class Settings(FolderNode):
    def build(self, config: Config) -> TREE:
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

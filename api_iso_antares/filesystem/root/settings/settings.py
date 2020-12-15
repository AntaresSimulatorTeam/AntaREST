from typing import Optional

from api_iso_antares.custom_types import JSON
from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.settings.comments import Comments
from api_iso_antares.filesystem.root.settings.generaldata import GeneralData
from api_iso_antares.filesystem.root.settings.resources.resources import (
    Resources,
)
from api_iso_antares.filesystem.root.settings.scenariobuilder import (
    ScenarioBuilder,
)
from api_iso_antares.filesystem.root.settings.simulations.simulations import (
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

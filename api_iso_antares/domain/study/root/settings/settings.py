from typing import Optional

from api_iso_antares.custom_types import JSON
from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.settings.comments import Comments
from api_iso_antares.domain.study.root.settings.generaldata import GeneralData
from api_iso_antares.domain.study.root.settings.resources.resources import (
    Resources,
)
from api_iso_antares.domain.study.root.settings.scenariobuilder import (
    ScenarioBuilder,
)


class Settings(FolderNode):
    def __init__(self, config: Config):
        children = {
            "resources": Resources(config.next_file("resources")),
            "comments": Comments(config.next_file("comments.txt")),
            "generaldata": GeneralData(config.next_file("generaldata.ini")),
            "scenariobuilder": ScenarioBuilder(
                config.next_file("scenariobuilder.dat")
            ),
        }
        FolderNode.__init__(self, children)

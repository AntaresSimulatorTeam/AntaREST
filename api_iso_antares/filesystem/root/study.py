from typing import Dict, Optional

from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.desktop import Desktop
from api_iso_antares.filesystem.root.input.input import Input
from api_iso_antares.filesystem.root.layers.layers import Layers
from api_iso_antares.filesystem.root.logs import Logs
from api_iso_antares.filesystem.root.output.output import Output
from api_iso_antares.filesystem.root.settings.settings import Settings
from api_iso_antares.filesystem.root.study_antares import StudyAntares
from api_iso_antares.filesystem.root.user import User


class Study(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "Desktop": Desktop(config.next_file("Desktop.ini")),
            "study": StudyAntares(config.next_file("study.antares")),
            "settings": Settings(config.next_file("settings")),
            "layers": Layers(config.next_file("layers")),
            "logs": Logs(config.next_file("logs")),
            "input": Input(config.next_file("input")),
            "user": User(config.next_file("user")),
        }

        if config.outputs:
            children["output"] = Output(config.next_file("output"))

        return children

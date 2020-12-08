from typing import Dict, Optional

from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.desktop import Desktop
from api_iso_antares.domain.study.root.input.input import Input
from api_iso_antares.domain.study.root.layers.layers import Layers
from api_iso_antares.domain.study.root.logs.logs import Logs
from api_iso_antares.domain.study.root.output.output import Output
from api_iso_antares.domain.study.root.settings.settings import Settings
from api_iso_antares.domain.study.root.study_antares import StudyAntares


class Study(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "desktop": Desktop(config.next_file("Desktop.ini")),
            "study": StudyAntares(config.next_file("study.antares")),
            "settings": Settings(config.next_file("settings")),
            "layers": Layers(config.next_file("layers")),
            "logs": Logs(config.next_file("logs")),
            "input": Input(config.next_file("input")),
            "output": Output(config.next_file("output")),
        }
        FolderNode.__init__(self, children)

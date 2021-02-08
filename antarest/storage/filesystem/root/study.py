from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.desktop import Desktop
from antarest.storage.filesystem.root.input.input import Input
from antarest.storage.filesystem.root.layers.layers import Layers
from antarest.storage.filesystem.root.logs import Logs
from antarest.storage.filesystem.root.output.output import Output
from antarest.storage.filesystem.root.settings.settings import Settings
from antarest.storage.filesystem.root.study_antares import StudyAntares
from antarest.storage.filesystem.root.user import User


class Study(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
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

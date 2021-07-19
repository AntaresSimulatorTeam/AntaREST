from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.desktop import Desktop
from antarest.storage.repository.filesystem.root.input.input import Input
from antarest.storage.repository.filesystem.root.layers.layers import Layers
from antarest.storage.repository.filesystem.root.logs import Logs
from antarest.storage.repository.filesystem.root.output.output import Output
from antarest.storage.repository.filesystem.root.settings.settings import (
    Settings,
)
from antarest.storage.repository.filesystem.root.study_antares import (
    StudyAntares,
)
from antarest.storage.repository.filesystem.root.user import User


class FileStudyTree(FolderNode):
    """
    Top level node of antares tree structure
    """

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "Desktop": Desktop(self.context, config.next_file("Desktop.ini")),
            "study": StudyAntares(
                self.context, config.next_file("study.antares")
            ),
            "settings": Settings(self.context, config.next_file("settings")),
            "layers": Layers(self.context, config.next_file("layers")),
            "logs": Logs(self.context, config.next_file("logs")),
            "input": Input(self.context, config.next_file("input")),
            "user": User(self.context, config.next_file("user")),
        }

        if config.outputs:
            children["output"] = Output(
                self.context, config.next_file("output")
            )

        return children

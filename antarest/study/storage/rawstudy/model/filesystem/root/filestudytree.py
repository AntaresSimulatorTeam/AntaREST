from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.desktop import (
    Desktop,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.input import (
    Input,
)
from antarest.study.storage.rawstudy.model.filesystem.root.layers.layers import (
    Layers,
)
from antarest.study.storage.rawstudy.model.filesystem.root.logs import Logs
from antarest.study.storage.rawstudy.model.filesystem.root.output.output import (
    Output,
)
from antarest.study.storage.rawstudy.model.filesystem.root.settings.settings import (
    Settings,
)
from antarest.study.storage.rawstudy.model.filesystem.root.study_antares import (
    StudyAntares,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user import User


class FileStudyTree(FolderNode):
    """
    Top level node of antares tree structure
    """

    def build(self, config: FileStudyTreeConfig) -> TREE:
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

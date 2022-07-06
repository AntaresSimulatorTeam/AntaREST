import logging
from threading import Thread

from antarest.core.utils.fastapi_sqlalchemy import db
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
from antarest.study.storage.rawstudy.model.filesystem.root.user.user import (
    User,
)


logger = logging.getLogger(__name__)


class FileStudyTree(FolderNode):
    """
    Top level node of antares tree structure
    """

    def build(self) -> TREE:
        children: TREE = {
            "Desktop": Desktop(
                self.context, self.config.next_file("Desktop.ini")
            ),
            "study": StudyAntares(
                self.context, self.config.next_file("study.antares")
            ),
            "settings": Settings(
                self.context, self.config.next_file("settings")
            ),
            "layers": Layers(self.context, self.config.next_file("layers")),
            "logs": Logs(self.context, self.config.next_file("logs")),
            "input": Input(self.context, self.config.next_file("input")),
            "user": User(self.context, self.config.next_file("user")),
        }

        if self.config.outputs:
            output_config = self.config.next_file("output")
            output_config.path = self.config.output_path or output_config.path
            children["output"] = Output(self.context, output_config)

        return children

    def async_denormalize(self) -> Thread:
        logger.info(
            f"Denormalizing (async) study data for study {self.config.study_id}"
        )
        thread = Thread(target=self._threaded_denormalize)
        thread.start()
        return thread

    def _threaded_denormalize(self) -> None:
        with db():
            self.denormalize()

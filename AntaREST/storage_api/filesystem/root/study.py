from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.desktop import Desktop
from AntaREST.storage_api.filesystem.root.input.input import Input
from AntaREST.storage_api.filesystem.root.layers.layers import Layers
from AntaREST.storage_api.filesystem.root.logs import Logs
from AntaREST.storage_api.filesystem.root.output.output import Output
from AntaREST.storage_api.filesystem.root.settings.settings import Settings
from AntaREST.storage_api.filesystem.root.study_antares import StudyAntares
from AntaREST.storage_api.filesystem.root.user import User


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

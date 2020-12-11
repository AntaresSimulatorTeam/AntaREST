from pathlib import Path

from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.logs.logs_item import LogsItem


class Logs(FolderNode):
    def __init__(self, config: Config):
        # TODO force simulations list
        children: TREE = {
            Logs.keep_name(file): LogsItem(config.next_file(file.name))
            for file in config.path.iterdir()
        }
        FolderNode.__init__(self, config, children)

    @staticmethod
    def keep_name(file: Path):
        return ".".join(file.name.split(".")[:-1])

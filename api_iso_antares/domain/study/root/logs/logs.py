from pathlib import Path

from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.logs.logs_item import LogsItem


class Logs(FolderNode):
    def __init__(self, config: Config):
        # TODO force simulations list
        children = {
            Logs.keep_name(file): LogsItem(config.next_file(file.name))
            for file in config.path.iterdir()
        }
        FolderNode.__init__(self, children)

    @staticmethod
    def keep_name(file: Path):
        return ".".join(file.name.split(".")[:-1])

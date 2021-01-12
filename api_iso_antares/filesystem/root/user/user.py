import glob
import os

from api_iso_antares.custom_types import JSON
from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.raw_file_node import RawFileNode
from api_iso_antares.filesystem.root.user.area import UserArea


class User(FolderNode):
    def build(self, config: Config) -> TREE:
        curr = os.curdir
        os.chdir(config.path)

        children: TREE = {
            path: RawFileNode(config.next_file(path))
            for path in glob.glob("**", recursive=True)
        }

        os.chdir(curr)
        return children

    def validate(self, data: JSON) -> None:
        pass
